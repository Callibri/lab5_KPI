from fastapi import APIRouter, Depends, HTTPException, Query, Request

from boxoffice.modules.analytics.contract import AnalyticsApi
from boxoffice.shared.web import require_user

router = APIRouter(tags=["analytics"], dependencies=[Depends(require_user)])


def get_api(request: Request) -> AnalyticsApi:
    return request.app.state.analytics_api


@router.get("/movies/{movie_id}/summary")
def movie_summary(movie_id: int, api: AnalyticsApi = Depends(get_api)):
    summary = api.movie_summary(movie_id)
    if summary is None:
        raise HTTPException(404, "Movie is not (yet) known to analytics")
    return summary


@router.get("/analytics/top")
def top_movies(limit: int = Query(10, ge=1, le=50), api: AnalyticsApi = Depends(get_api)):
    return api.top_movies(limit)


@router.get("/analytics/regions")
def revenue_by_region(api: AnalyticsApi = Depends(get_api)):
    return api.revenue_by_region()
