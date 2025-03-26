# Facebook Post Metrics
AVAILABLE_METRICS = {
    'impressions': 'post_impressions',
    'reach': 'post_impressions_unique',
    'engaged_users': 'post_engaged_users',
    'reactions': 'post_reactions_by_type_total',
    'clicks': 'post_clicks',
    'like': 'post_reactions_like_total',
    'love': 'post_reactions_love_total',
    'wow': 'post_reactions_wow_total',
    'haha': 'post_reactions_haha_total',
    'sorry': 'post_reactions_sorry_total',
    'anger': 'post_reactions_anger_total',
    'video_views': 'post_video_views',
    'video_views_10s': 'post_video_views_10s',
    'video_avg_time_watched': 'post_video_avg_time_watched',
    'video_length': 'post_video_length',
    'total_video_views_unique': 'total_video_views_unique',
    'total_video_impressions': 'total_video_impressions',
    'total_video_view_time': 'total_video_view_time',
    'total_video_complete_views': 'total_video_complete_views',
    'total_video_avg_time_watched': 'total_video_avg_time_watched',
    'total_video_views_autoplayed': 'total_video_views_autoplayed',
    'total_video_views_clicked_to_play': 'total_video_views_clicked_to_play',
    'total_video_views_sound_on': 'total_video_views_sound_on',
    'link_clicks': 'post_clicks_by_type',
    'negative_feedback': 'post_negative_feedback'
}

# Facebook Reel Metrics
AVAILABLE_REEL_METRICS = {
    'reels_total_number_milliseconds': 'post_video_view_time',
    'reels_total_comment_share': 'post_video_social_actions',
    'reactions': 'post_video_likes_by_reaction_type',
    'reach': 'post_impressions_unique',
    'impressions': 'fb_reels_total_plays',
    'like': 'post_video_likes_by_reaction_type',
    'love': 'post_video_likes_by_reaction_type',
    'wow': 'post_video_likes_by_reaction_type',
    'haha': 'post_video_likes_by_reaction_type',
    'sorry': 'post_video_likes_by_reaction_type',
    'anger': 'post_video_likes_by_reaction_type',
}

DEFAULT_REEL_METRICS = [
    'reels_total_number_milliseconds',
    'reels_total_comment_share',
    'reactions',
    'reach',
    'impressions',
    'like',
    'love',
    'wow',
    'haha',
    'sorry',
    'anger'
]

# Facebook Ads Metrics
ADS_METRICS = {
    'impressions': 'impressions',
    'reach': 'reach',
    'frequency': 'frequency',
    'clicks': 'clicks',
    'unique_clicks': 'unique_clicks',
    'ctr': 'ctr',
    'unique_ctr': 'unique_ctr',
    'cpc': 'cpc',
    'cpm': 'cpm',
    'cpp': 'cpp',
    'spend': 'spend',
    'social_spend': 'social_spend',
    'actions': 'actions',
    'action_values': 'action_values',
    'conversions': 'conversions',
    'cost_per_action_type': 'cost_per_action_type',
    'cost_per_unique_click': 'cost_per_unique_click',
    'cost_per_inline_link_click': 'cost_per_inline_link_click',
    'cost_per_inline_post_engagement': 'cost_per_inline_post_engagement',
    'website_ctr': 'website_ctr',
    'website_purchases': 'website_purchases',
    'purchases': 'purchases',
    'purchase_roas': 'purchase_roas',
    'leads': 'leads',
    'cost_per_lead': 'cost_per_lead'
}

# Facebook Ads Dimensions
ADS_DIMENSIONS = {
    'account_id': 'account_id',
    'account_name': 'account_name',
    'ad_id': 'ad_id',
    'ad_name': 'ad_name',
    'adset_id': 'adset_id',
    'adset_name': 'adset_name',
    'campaign_id': 'campaign_id',
    'campaign_name': 'campaign_name',
    'age': 'age',
    'country': 'country',
    'gender': 'gender',
    'impression_device': 'impression_device',
    'publisher_platform': 'publisher_platform',
    'platform_position': 'platform_position',
    'device_platform': 'device_platform',
    'region': 'region'
}

# Google Ads Metrics
GOOGLE_ADS_METRICS = {
    'impressions': 'metrics.impressions',
    'clicks': 'metrics.clicks',
    'cost_micros': 'metrics.cost_micros',
    'ctr': 'metrics.ctr',
    'average_cpc': 'metrics.average_cpc',
    'conversions': 'metrics.conversions',
    'cost_per_conversion': 'metrics.cost_per_conversion',
    'conversion_rate': 'metrics.conversion_rate',
    'all_conversions': 'metrics.all_conversions',
    'all_conversion_value': 'metrics.all_conversion_value',
    'video_views': 'metrics.video_views',
    'average_cpm': 'metrics.average_cpm',
    'interactions': 'metrics.interactions',
    'interaction_rate': 'metrics.interaction_rate'
}

# Google Ads Dimensions
GOOGLE_ADS_DIMENSIONS = {
    'date': 'segments.date',
    'device': 'segments.device',
    'day_of_week': 'segments.day_of_week',
    'ad_network_type': 'segments.ad_network_type',
    'click_type': 'segments.click_type',
    'conversion_action': 'segments.conversion_action'
}

# Default metrics for Google Ads
DEFAULT_GOOGLE_ADS_METRICS = [
    'impressions',
    'clicks',
    'cost_micros',
    'ctr',
    'average_cpc',
    'conversions'
]

# Default dimensions for Google Ads
DEFAULT_GOOGLE_ADS_DIMENSIONS = [
    'date',
    'device',
    'ad_network_type'
] 