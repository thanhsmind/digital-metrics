Bạn là một software engineer hiểu sâu về python, fastapi, facebook sdk, google sdk, cẩn thận và chi tiết trong dự án Digital Metrics.
we have some issues in the codebase.

your goal is to fix my issues
when i run api
/api/v1/facebook/business_posts_and_reels_insights_csv?business_id=1602411516748597&post_metrics=impressions%2Creach%2Cengaged_users%2Cclick&reel_metrics=impressions%2Creach%2Creaction&since_date=2024-02-21&until_date=2024-03-21&token=EAAQHgrXRCI4BOwU7J9OwNSKbtQJ0xlKpEu8feZB1tWCXcAOOIy1BRtarYHoKGpOz9nB65vItsVaAOHj2L6pphu5Y0mcUsmmAcnjS7tN4Ayi6a4ZA1zoDz8AtRFnNXEZAZBCD8i4iCsHT9v2NW5ipQa6X0ZBjCqXyagnZAe9PqzNQgb2EldJbkjQtVxpfsEJwKRzaQLE0ZCJyL2ApkVsYsBnMbVZCXsRbkId5SF2pt7pZCfNSAtJJwIcdVs9cd86LcN9eTBwZDZD

<problems>

TypeError: FacebookAdsApi.call() got an unexpected keyword argument 'fields'
ERROR:app.services.facebook_ads:Unexpected error fetching insights for video 423835093474247: FacebookAdsApi.call() got an unexpected keyword argument 'fields'
Traceback (most recent call last):
File "D:\projects\digital-metrics\app\services\facebook_ads.py", line 644, in fetch_single_video_insights
insights_result = await asyncio.to_thread(
^^^^^^^^^^^^^^^^^^^^^^^^
File "C:\ProgramData\miniconda3\Lib\asyncio\threads.py", line 25, in to_thread
return await loop.run_in_executor(None, func_call)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "C:\ProgramData\miniconda3\Lib\concurrent\futures\thread.py", line 59, in run
result = self.fn(\*self.args, \*\*self.kwargs)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "D:\projects\digital-metrics\app\services\facebook_ads.py", line 65, in get_insights
return self.api.call("GET", path, params=params, fields=fields)
</problems>

This is the Technical Design Document we are currently working on:

<story>

</story>

Output:

- output every file which has been changed + filename
