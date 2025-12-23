import dlt
import logging
from typing import Dict, List, Any, Iterator, Optional, Callable
from datetime import datetime, timezone
from .hubspot_api_service import HubSpotAPIService
from loki_logger import get_logger, log_business_event, log_security_event
import uuid
from decimal import Decimal


def transform_hubspot_deal(deal: Dict[str, Any], scan_id: str, tenant_id: Optional[str], page_number: int) -> Dict[str, Any]:
    """
    Transform HubSpot deal data to our database schema
    
    Args:
        deal: Raw HubSpot deal data
        scan_id: Scan identifier
        tenant_id: Tenant identifier
        page_number: Current page number
    
    Returns:
        Transformed deal data matching our database schema
    """
    properties = deal.get("properties", {})
    
    # Parse amount safely
    amount = None
    if properties.get("amount"):
        try:
            amount = float(properties["amount"])
        except (ValueError, TypeError):
            amount = None
    
    # Parse dates safely
    def parse_date(date_str):
        if not date_str:
            return None
        try:
            # HubSpot dates are in ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None
    
    # Parse probability safely
    probability = None
    if properties.get("hs_deal_stage_probability"):
        try:
            probability = float(properties["hs_deal_stage_probability"]) / 100.0  # Convert percentage to decimal
        except (ValueError, TypeError):
            probability = None
    
    return {
        "id": str(uuid.uuid4()),  # Generate unique ID for our database
        "deal_id": deal.get("id"),  # HubSpot deal ID
        "deal_name": properties.get("dealname"),
        "amount": amount,
        "deal_stage": properties.get("dealstage"),
        "close_date": parse_date(properties.get("closedate")),
        "pipeline": properties.get("pipeline"),
        "deal_type": properties.get("dealtype"),
        "hubspot_owner_id": properties.get("hubspot_owner_id"),
        "deal_stage_probability": probability,
        "description": properties.get("description"),
        "analytics_source": properties.get("hs_analytics_source"),
        "num_associated_contacts": int(properties.get("num_associated_contacts", 0)) if properties.get("num_associated_contacts") else 0,
        "priority": properties.get("hs_priority"),
        "next_step": properties.get("hs_next_step"),
        "forecast_amount": float(properties.get("hs_forecast_amount")) if properties.get("hs_forecast_amount") else None,
        "forecast_probability": float(properties.get("hs_forecast_probability")) if properties.get("hs_forecast_probability") else None,
        "hubspot_created_at": parse_date(properties.get("createdate")),
        "hubspot_updated_at": parse_date(properties.get("hs_lastmodifieddate")),
        "archived": deal.get("archived", False),
        "raw_properties": properties,  # Store complete properties as JSON
        "_extracted_at": datetime.now(timezone.utc),
        "_scan_id": scan_id,
        "_tenant_id": tenant_id,
        "_page_number": page_number,
        "_source_service": "hubspot_deals"
    }

def create_data_source(
    job_config: Dict[str, Any],
    auth_config: Dict[str, Any],
    filters: Dict[str, Any],
    checkpoint_callback: Optional[Callable] = None,
    check_cancel_callback: Optional[Callable] = None,
    check_pause_callback: Optional[Callable] = None,
    resume_from: Optional[Dict[str, Any]] = None,
):
    """
    Create DLT source function for HubSpot Deals data extraction with checkpoint support
    """
    logger = get_logger(__name__)
    
    # Get access token from auth config
    access_token = auth_config.get("access_token") or auth_config.get("accessToken")
    if not access_token:
        raise ValueError("No access token found in auth configuration")
    
    # Initialize HubSpot API service
    api_service = HubSpotAPIService(access_token=access_token)
    
    # Validate credentials
    if not api_service.validate_credentials():
        raise ValueError("Invalid HubSpot access token or insufficient permissions")
    
    # Get configuration
    tenant_id = job_config.get("tenant_id") or job_config.get("organizationId")
    scan_id = filters.get("scan_id", "unknown")
    
    logger.info(
        "Starting HubSpot Deals data extraction",
        extra={
            "operation": "data_source_init",
            "tenant_id": tenant_id,
            "scan_id": scan_id,
            "filters": filters,
            "has_resume_data": resume_from is not None
        },
    )

    @dlt.resource(name="hubspot_deals", write_disposition="replace", primary_key="deal_id")
    def get_hubspot_deals() -> Iterator[Dict[str, Any]]:
        """
        Extract HubSpot deals data with checkpoint support and pagination
        """

        # Initialize state
        if resume_from:
            after = resume_from.get("cursor")
            page_count = resume_from.get("page_number", 0)
            total_records = resume_from.get("records_processed", 0)
            logger.info(
                "Resuming HubSpot deals extraction",
                extra={
                    "operation": "hubspot_deals_extraction",
                    "page_number": page_count + 1,
                    "total_processed": total_records,
                    "cursor": after
                },
            )
        else:
            after = None
            page_count = 0
            total_records = 0
            logger.info(
                "Starting fresh HubSpot deals extraction",
                extra={"operation": "hubspot_deals_extraction", "scan_id": scan_id},
            )

        # Configuration
        checkpoint_interval = 5  # Save checkpoint every 5 pages (500 deals)
        cancel_check_interval = 1
        pause_check_interval = 1
        batch_size = 100  # HubSpot API limit
        
        # Extract filter parameters
        properties = filters.get("properties")
        archived = filters.get("archived", False)
        deal_stages = filters.get("dealStages")
        pipelines = filters.get("pipelines")

        while page_count < 1000:  # Safety limit
            try:
                # Check for cancellation
                if page_count % cancel_check_interval == 0:
                    if check_cancel_callback and check_cancel_callback(scan_id):
                        logger.info(
                            "HubSpot deals extraction cancelled by user",
                            extra={
                                "operation": "hubspot_deals_extraction",
                                "scan_id": scan_id,
                                "page_number": page_count + 1,
                                "total_processed": total_records,
                            },
                        )

                        # Save cancellation checkpoint
                        if checkpoint_callback:
                            try:
                                cancel_checkpoint = {
                                    "phase": "hubspot_deals_cancelled",
                                    "records_processed": total_records,
                                    "cursor": after,
                                    "page_number": page_count,
                                    "batch_size": batch_size,
                                    "checkpoint_data": {
                                        "cancellation_reason": "user_requested",
                                        "cancelled_at_page": page_count,
                                        "service": "hubspot_deals",
                                    },
                                }
                                checkpoint_callback(scan_id, cancel_checkpoint)
                            except Exception as e:
                                logger.warning(
                                    "Failed to save cancellation checkpoint",
                                    extra={"scan_id": scan_id, "error": str(e)},
                                )
                        break

                # Check for pause request
                if page_count % pause_check_interval == 0:
                    if check_pause_callback and check_pause_callback(scan_id):
                        logger.info(
                            "HubSpot deals extraction paused by user",
                            extra={
                                "operation": "hubspot_deals_extraction",
                                "scan_id": scan_id,
                                "page_number": page_count + 1,
                                "total_processed": total_records,
                            },
                        )

                        # Save pause checkpoint
                        if checkpoint_callback:
                            try:
                                pause_checkpoint = {
                                    "phase": "hubspot_deals_paused",
                                    "records_processed": total_records,
                                    "cursor": after,
                                    "page_number": page_count,
                                    "batch_size": batch_size,
                                    "checkpoint_data": {
                                        "pause_reason": "user_requested",
                                        "paused_at_page": page_count,
                                        "paused_at": datetime.now(timezone.utc).isoformat(),
                                        "service": "hubspot_deals",
                                    },
                                }
                                checkpoint_callback(scan_id, pause_checkpoint)

                                logger.info(
                                    "Pause checkpoint saved",
                                    extra={
                                        "operation": "hubspot_deals_extraction",
                                        "scan_id": scan_id,
                                        "page_number": page_count,
                                        "total_processed": total_records,
                                    },
                                )
                            except Exception as e:
                                logger.warning(
                                    "Failed to save pause checkpoint",
                                    extra={"scan_id": scan_id, "error": str(e)},
                                )

                        # Exit gracefully
                        break

                logger.debug(
                    "Fetching HubSpot deals page",
                    extra={
                        "operation": "hubspot_deals_extraction",
                        "scan_id": scan_id,
                        "page_number": page_count + 1,
                        "cursor": after
                    },
                )

                # Fetch deals from HubSpot API
                data = api_service.get_deals(
                    limit=batch_size,
                    after=after,
                    properties=properties,
                    archived=archived
                )

                page_records = 0
                deals = data.get("results", [])
                
                if deals:
                    for deal in deals:
                        # Check for pause/cancel during record processing
                        if check_pause_callback and check_pause_callback(scan_id):
                            logger.info(
                                "HubSpot deals extraction paused mid-page",
                                extra={
                                    "operation": "hubspot_deals_extraction",
                                    "scan_id": scan_id,
                                    "page_number": page_count + 1,
                                    "records_in_page": page_records,
                                    "total_processed": total_records + page_records,
                                },
                            )

                            # Save mid-page pause checkpoint
                            if checkpoint_callback:
                                try:
                                    mid_page_checkpoint = {
                                        "phase": "hubspot_deals_paused_mid_page",
                                        "records_processed": total_records + page_records,
                                        "cursor": after,
                                        "page_number": page_count,
                                        "batch_size": batch_size,
                                        "checkpoint_data": {
                                            "pause_reason": "user_requested_mid_page",
                                            "paused_at_page": page_count,
                                            "records_completed_in_page": page_records,
                                            "paused_at": datetime.now(timezone.utc).isoformat(),
                                            "service": "hubspot_deals",
                                        },
                                    }
                                    checkpoint_callback(scan_id, mid_page_checkpoint)
                                except Exception as e:
                                    logger.warning(
                                        "Failed to save mid-page pause checkpoint",
                                        extra={"scan_id": scan_id, "error": str(e)},
                                    )
                            return

                        # Transform HubSpot deal to our schema
                        transformed_deal = transform_hubspot_deal(deal, scan_id, tenant_id, page_count + 1)
                        
                        # Apply filters if specified
                        if deal_stages and transformed_deal.get("deal_stage") not in deal_stages:
                            continue
                        
                        if pipelines and transformed_deal.get("pipeline") not in pipelines:
                            continue

                        yield transformed_deal
                        page_records += 1

                # Update counters
                total_records += page_records
                page_count += 1

                # Save checkpoint periodically
                if checkpoint_callback and page_count % checkpoint_interval == 0:
                    try:
                        # Get next cursor from HubSpot pagination
                        next_cursor = None
                        paging = data.get("paging", {})
                        if paging.get("next") and paging["next"].get("after"):
                            next_cursor = paging["next"]["after"]

                        checkpoint_data = {
                            "phase": "hubspot_deals_processing",
                            "records_processed": total_records,
                            "cursor": next_cursor,
                            "page_number": page_count,
                            "batch_size": batch_size,
                            "checkpoint_data": {
                                "pages_processed": page_count,
                                "last_page_records": page_records,
                                "service": "hubspot_deals",
                                "has_more_pages": next_cursor is not None
                            },
                        }

                        checkpoint_callback(scan_id, checkpoint_data)

                        logger.debug(
                            "HubSpot deals checkpoint saved",
                            extra={
                                "operation": "hubspot_deals_extraction",
                                "scan_id": scan_id,
                                "page_number": page_count,
                                "total_records": total_records,
                                "next_cursor": next_cursor
                            },
                        )

                    except Exception as checkpoint_error:
                        logger.warning(
                            "Failed to save HubSpot deals checkpoint",
                            extra={
                                "operation": "hubspot_deals_extraction",
                                "scan_id": scan_id,
                                "error": str(checkpoint_error),
                            },
                        )

                # Handle HubSpot pagination
                paging = data.get("paging", {})
                if paging.get("next") and paging["next"].get("after"):
                    after = paging["next"]["after"]
                else:
                    # Final checkpoint on completion
                    if checkpoint_callback:
                        try:
                            final_checkpoint = {
                                "phase": "hubspot_deals_completed",
                                "records_processed": total_records,
                                "cursor": None,
                                "page_number": page_count,
                                "batch_size": batch_size,
                                "checkpoint_data": {
                                    "completion_status": "success",
                                    "total_pages": page_count,
                                    "final_total": total_records,
                                    "service": "hubspot_deals",
                                },
                            }
                            checkpoint_callback(scan_id, final_checkpoint)
                        except Exception as e:
                            logger.warning(
                                "Failed to save final checkpoint",
                                extra={"scan_id": scan_id, "error": str(e)},
                            )

                    logger.info(
                        "HubSpot deals extraction completed",
                        extra={
                            "operation": "hubspot_deals_extraction",
                            "scan_id": scan_id,
                            "total_records": total_records,
                            "total_pages": page_count,
                        },
                    )
                    break

            except Exception as e:
                logger.error(
                    "Error fetching HubSpot deals page",
                    extra={
                        "operation": "hubspot_deals_extraction",
                        "scan_id": scan_id,
                        "page_number": page_count + 1,
                        "error": str(e),
                    },
                    exc_info=True,
                )

                # Save error checkpoint for debugging
                if checkpoint_callback:
                    try:
                        error_checkpoint = {
                            "phase": "hubspot_deals_error",
                            "records_processed": total_records,
                            "cursor": after,
                            "page_number": page_count,
                            "batch_size": batch_size,
                            "checkpoint_data": {
                                "error": str(e),
                                "error_page": page_count + 1,
                                "recovery_cursor": after,
                                "service": "hubspot_deals",
                            },
                        }
                        checkpoint_callback(scan_id, error_checkpoint)
                    except:
                        pass

                raise e

    return [get_hubspot_deals]