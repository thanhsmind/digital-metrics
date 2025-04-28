# Facebook Metrics Guide

This guide provides a comprehensive reference for all metrics available in the Facebook API endpoints.

## Post Metrics

### Default Post Metrics

These metrics are used by default in post-related endpoints if no specific metrics are requested:

```json
[
  "post_impressions",
  "post_impressions_unique",
  "post_engaged_users",
  "post_reactions_like_total",
  "post_clicks"
]
```

### Available Post Metrics

The following metrics can be requested for Facebook posts:

| Metric                           | Description                                                        |
| -------------------------------- | ------------------------------------------------------------------ |
| post_impressions                 | Total number of times the post was shown                           |
| post_impressions_unique          | Number of unique users who saw the post (Reach)                    |
| post_impressions_paid            | Number of times the post was shown through paid distribution       |
| post_impressions_organic         | Number of times the post was shown through unpaid distribution     |
| post_engaged_users               | Number of unique users who engaged with the post                   |
| post_clicks                      | Total number of clicks on the post                                 |
| post_clicks_unique               | Number of unique users who clicked on the post                     |
| post_reactions_like_total        | Number of "Like" reactions on the post                             |
| post_reactions_love_total        | Number of "Love" reactions on the post                             |
| post_reactions_wow_total         | Number of "Wow" reactions on the post                              |
| post_reactions_haha_total        | Number of "Haha" reactions on the post                             |
| post_reactions_sorry_total       | Number of "Sorry" reactions on the post                            |
| post_reactions_anger_total       | Number of "Anger" reactions on the post                            |
| post_negative_feedback           | Number of times people took a negative action on the post          |
| post_negative_feedback_unique    | Number of unique users who took negative actions                   |
| post_engaged_fan                 | Number of unique fans who engaged with the post                    |
| post_video_avg_time_watched      | Average time users spent watching your video                       |
| post_video_views                 | Number of times your video was viewed for 3 seconds or more        |
| post_video_views_paid            | Number of paid views of 3 seconds or more                          |
| post_video_views_organic         | Number of organic views of 3 seconds or more                       |
| post_video_views_unique          | Number of unique users who viewed your video for 3 seconds or more |
| post_video_views_autoplayed      | Number of autoplayed video views                                   |
| post_video_views_clicked_to_play | Number of video views that were clicked to play                    |
| post_video_view_time             | Total time spent watching your video                               |

## Reel Metrics

### Default Reel Metrics

These metrics are used by default in reel-related endpoints if no specific metrics are requested:

```json
[
  "total_video_views",
  "total_video_avg_watch_time",
  "reach",
  "likes",
  "comments",
  "shares",
  "saved"
]
```

### Available Reel Metrics

The following metrics can be requested for Facebook reels:

| Metric                         | Description                                |
| ------------------------------ | ------------------------------------------ |
| total_video_views              | Total number of times the reel was played  |
| total_video_views_unique       | Number of unique users who viewed the reel |
| total_video_avg_watch_time     | Average time users spent watching the reel |
| total_video_impressions        | Number of times the reel was shown         |
| total_video_impressions_unique | Number of unique users who saw the reel    |
| reach                          | Number of unique users who saw the reel    |
| likes                          | Number of likes on the reel                |
| comments                       | Number of comments on the reel             |
| shares                         | Number of times the reel was shared        |
| saved                          | Number of times the reel was saved         |

## Campaign Metrics

### Default Campaign Metrics

These metrics are used by default in campaign-related endpoints if no specific metrics are requested:

```json
["spend", "impressions", "reach", "clicks", "ctr", "cpc"]
```

### Available Campaign Metrics

The following metrics can be requested for Facebook ad campaigns:

| Metric                         | Description                                     |
| ------------------------------ | ----------------------------------------------- |
| impressions                    | Number of times your ads were shown             |
| reach                          | Number of unique people who saw your ads        |
| frequency                      | Average number of times each person saw your ad |
| spend                          | Amount spent in the account currency            |
| clicks                         | Number of clicks on your ads                    |
| ctr                            | Click-through rate (clicks/impressions)         |
| cpc                            | Average cost per click                          |
| cpm                            | Average cost per 1,000 impressions              |
| cpp                            | Average cost per result based on your objective |
| conversions                    | Number of conversions attributed to your ads    |
| cost_per_conversion            | Average cost per conversion                     |
| video_p25_watched_actions      | Number of times your video was played to 25%    |
| video_p50_watched_actions      | Number of times your video was played to 50%    |
| video_p75_watched_actions      | Number of times your video was played to 75%    |
| video_p100_watched_actions     | Number of times your video was played to 100%   |
| video_avg_time_watched_actions | Average viewing time of your video              |

## Usage Example

When requesting metrics, you can specify multiple metrics separated by commas:

```
GET /facebook/business_post_insights_csv?business_id=123456789&metrics=post_impressions,post_engaged_users,post_reactions_like_total&since_date=2024-03-01&until_date=2024-03-31
```

If no metrics are specified, the default metrics for that content type will be used.

## Notes

1. Not all metrics may be available for all content types or time periods
2. Some metrics may require specific permissions
3. Metric availability can change based on Facebook API updates
4. Invalid metrics will be ignored with a warning
