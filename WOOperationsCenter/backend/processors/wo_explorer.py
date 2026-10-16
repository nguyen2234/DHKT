"""
Work Order Explorer Processor.
Provides fast in-memory search, filtering, sorting, and pagination
for all Work Orders across all centers.
"""

from typing import Any, Dict, List, Optional
from backend.domain.models import ReportDataset, WorkOrder


class WOExplorerProcessor:
    """Handles query, filter, sort and pagination for Work Orders."""

    @classmethod
    def query_work_orders(
        cls,
        dataset: ReportDataset,
        center_code: Optional[str] = None,
        classification: Optional[str] = None,  # 'all', 'overdue', 'pending', 'boundary'
        search_query: Optional[str] = None,
        job_type: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "overdue_days",
        sort_order: str = "asc",  # 'asc' or 'desc'
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Queries work orders matching criteria with pagination.
        """
        # Gather candidate work orders
        target_centers = [dataset.centers[center_code]] if (center_code and center_code in dataset.centers) else list(dataset.centers.values())

        candidates: List[WorkOrder] = []
        for c in target_centers:
            if not classification or classification.lower() == "all":
                candidates.extend(c.work_orders)
                candidates.extend(c.pending_work_orders)
                candidates.extend(c.boundary_work_orders)
            elif classification.lower() == "overdue":
                candidates.extend(c.work_orders)
            elif classification.lower() == "pending":
                candidates.extend(c.pending_work_orders)
            elif classification.lower() == "boundary":
                candidates.extend(c.boundary_work_orders)

        # Apply search query
        if search_query:
            q = search_query.strip().lower()
            filtered = []
            for w in candidates:
                if (
                    q in w.code.lower() or
                    q in w.performer.lower() or
                    q in w.station_code.lower() or
                    q in w.content.lower() or
                    (w.ft_comment and q in w.ft_comment.lower()) or
                    (w.ft_mobile and q in w.ft_mobile.lower()) or
                    q in w.center_code.lower() or
                    q in w.center_name.lower()
                ):
                    filtered.append(w)
            candidates = filtered

        # Apply job type filter
        if job_type and job_type.lower() != "all":
            candidates = [w for w in candidates if job_type.lower() in w.job_type.lower()]

        # Apply status filter
        if status and status.lower() != "all":
            candidates = [w for w in candidates if status.lower() in w.status.lower()]

        total_matching = len(candidates)

        # Sorting helper
        def sort_key(w: WorkOrder):
            if sort_by == "overdue_days":
                try:
                    return float(w.overdue_days) if w.overdue_days is not None else 0.0
                except (ValueError, TypeError):
                    return 0.0
            elif sort_by == "performer":
                return w.performer.lower()
            elif sort_by == "code":
                return w.code.lower()
            elif sort_by == "deadline":
                return str(w.deadline)
            elif sort_by == "station":
                return w.station_code.lower()
            return w.code.lower()

        reverse_sort = (sort_order.lower() == "desc")
        candidates.sort(key=sort_key, reverse=reverse_sort)

        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = candidates[start_idx:end_idx]

        # Convert to serialized dicts
        items_data = []
        for w in page_items:
            items_data.append({
                "stt": w.stt,
                "code": w.code,
                "job_type": w.job_type,
                "content": w.content,
                "deadline": w.deadline,
                "status": w.status,
                "performer": w.performer,
                "station_code": w.station_code,
                "ft_comment": w.ft_comment or "",
                "ft_mobile": w.ft_mobile or "",
                "completed_date": str(w.completed_date or ""),
                "overdue_days": w.overdue_days,
                "center_code": w.center_code,
                "center_name": w.center_name,
                "bkk": w.bkk or "",
                "bkk_reason": w.bkk_reason or "",
                "classification": w.classification
            })

        return {
            "total": total_matching,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_matching + page_size - 1) // page_size if page_size > 0 else 1,
            "items": items_data
        }
