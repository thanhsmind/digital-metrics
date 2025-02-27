import csv
import json
import logging
from datetime import datetime, timedelta
from io import StringIO
from typing import Dict, List, Optional

import requests
import uvicorn
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.post import Post
from facebook_business.adobjects.user import User
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

CONFIG_FILE = 'config.json'


def load_config(file_path=CONFIG_FILE):
    with open(file_path, 'r') as config_file:
        return json.load(config_file)

def save_config(config, file_path=CONFIG_FILE):
    with open(file_path, 'w') as config_file:
        json.dump(config, config_file, indent=2)

config = load_config()

debug_mode = config.get('debug_mode', True)

def custom_logger(message, level=logging.INFO):
    if debug_mode or level >= logging.WARNING:
        if level == logging.DEBUG:
            logging.debug(message)
        elif level == logging.INFO:
            logging.info(message)
        elif level == logging.WARNING:
            logging.warning(message)
        elif level == logging.ERROR:
            logging.error(message)
        elif level == logging.CRITICAL:
            logging.critical(message)

# Define available metrics for post insights
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

# Thêm vào đầu file, sau các AVAILABLE_METRICS khác

ADS_METRICS = {
    'impressions': 'impressions',
    'reach': 'reach',
    'frequency': 'frequency',
    'clicks': 'clicks',
    'unique_clicks': 'unique_clicks',
    'ctr': 'ctr',  # Click-through rate
    'unique_ctr': 'unique_ctr',
    'cpc': 'cpc',  # Cost per click
    'cpm': 'cpm',  # Cost per 1,000 impressions
    'cpp': 'cpp',  # Cost per 1,000 people reached
    'spend': 'spend',
    'social_spend': 'social_spend',
    'actions': 'actions',
    'action_values': 'action_values',
    'conversions': 'conversions',
    'cost_per_action_type': 'cost_per_action_type',
    'cost_per_unique_click': 'cost_per_unique_click',
    'cost_per_inline_link_click': 'cost_per_inline_link_click',
    'cost_per_inline_post_engagement': 'cost_per_inline_post_engagement',
    'cost_per_unique_inline_link_click': 'cost_per_unique_inline_link_click',
    'cost_per_unique_outbound_click': 'cost_per_unique_outbound_click',
    'outbound_clicks': 'outbound_clicks',
    'outbound_clicks_ctr': 'outbound_clicks_ctr',
    'unique_outbound_clicks': 'unique_outbound_clicks',
    'unique_outbound_clicks_ctr': 'unique_outbound_clicks_ctr',
    'video_30_sec_watched_actions': 'video_30_sec_watched_actions',
    'video_p25_watched_actions': 'video_p25_watched_actions',
    'video_p50_watched_actions': 'video_p50_watched_actions',
    'video_p75_watched_actions': 'video_p75_watched_actions',
    'video_p100_watched_actions': 'video_p100_watched_actions',
    'video_avg_time_watched_actions': 'video_avg_time_watched_actions',
    'video_play_actions': 'video_play_actions',
    'website_ctr': 'website_ctr',
    'website_purchases': 'website_purchases',
    'mobile_app_purchases': 'mobile_app_purchases',
    'purchases': 'purchases',
    'purchase_roas': 'purchase_roas',  # Return on Ad Spend for purchases
    'landing_page_views': 'landing_page_views',
    'cost_per_landing_page_view': 'cost_per_landing_page_view',
    'leads': 'leads',
    'cost_per_lead': 'cost_per_lead',
    'ads_clicked': 'ads_clicked',
    'unique_inline_link_clicks': 'unique_inline_link_clicks',
    'inline_link_clicks': 'inline_link_clicks',
    'inline_link_click_ctr': 'inline_link_click_ctr',
    'inline_post_engagement': 'inline_post_engagement',
    'objective': 'objective',
    'relevance_score': 'relevance_score',
    'quality_ranking': 'quality_ranking',
    'engagement_rate_ranking': 'engagement_rate_ranking',
    'conversion_rate_ranking': 'conversion_rate_ranking',
    'estimated_ad_recallers': 'estimated_ad_recallers',
    'estimated_ad_recall_rate': 'estimated_ad_recall_rate',
    'cost_per_estimated_ad_recallers': 'cost_per_estimated_ad_recallers',
    'unique_link_clicks_ctr': 'unique_link_clicks_ctr',
    'cost_per_unique_inline_link_click': 'cost_per_unique_inline_link_click',
    'cost_per_2_sec_continuous_video_view': 'cost_per_2_sec_continuous_video_view',
    'cost_per_thruplay': 'cost_per_thruplay',
}

ADS_DIMENSIONS = {
    'account_id': 'account_id',
    'account_name': 'account_name',
    'ad_id': 'ad_id',
    'ad_name': 'ad_name',
    'adset_id': 'adset_id',
    'adset_name': 'adset_name',
    'campaign_id': 'campaign_id',
    'campaign_name': 'campaign_name',
    'ad_format_asset': 'ad_format_asset',
    'age': 'age',
    'country': 'country',
    'gender': 'gender',
    'impression_device': 'impression_device',
    'publisher_platform': 'publisher_platform',
    'platform_position': 'platform_position',
    'device_platform': 'device_platform',
    'region': 'region',
    'dma': 'dma',
    'frequency_value': 'frequency_value',
    'hourly_stats_aggregated_by_advertiser_time_zone': 'hourly_stats_aggregated_by_advertiser_time_zone',
    'hourly_stats_aggregated_by_audience_time_zone': 'hourly_stats_aggregated_by_audience_time_zone',
    'place_page_id': 'place_page_id',
    'product_id': 'product_id',
    'conversion_destination': 'conversion_destination'
}


class PageToken(BaseModel):
    page_id: str
    page_name: str
    access_token: str
    last_updated: str

class FacebookApiManager:
    def __init__(self, app_id, app_secret, access_token, api_version):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = access_token
        self.api_version = api_version
        self.refresh_attempts = 0
        self.page_tokens: Dict[str, PageToken] = self.load_page_tokens()
        self.init_api()
        self.api = FacebookAdsApi.get_default_api()  

    def init_api(self):
        self.api = FacebookAdsApi.init(app_id=self.app_id, 
                                    app_secret=self.app_secret, 
                                    access_token=self.access_token,
                                    api_version=self.api_version)
        FacebookAdsApi.set_default_api(self.api)
        custom_logger(f"Initialized Facebook API with version {self.api_version}", logging.INFO)

    def load_page_tokens(self):
        return {page_id: PageToken(**token_data) 
                for page_id, token_data in config.get('page_tokens', {}).items()}

    def save_page_tokens(self):
        config['page_tokens'] = {
            page_id: token.model_dump() for page_id, token in self.page_tokens.items()
        }
        save_config(config)
    
    def get_all_business_post_insights(self, business_id: str, metrics: List[str], since_date: str, until_date: str):
        try:
            FacebookAdsApi.init(access_token=self.access_token)
            business = Business(business_id)
            pages = business.get_owned_pages(fields=['id', 'name'])
            
            all_insights = []
            for page in pages:
                page_data = page.export_all_data()
                page_id = page_data['id']
                page_name = page_data['name']
                
                if page_id not in self.page_tokens:
                    custom_logger(f"Không có token cho trang {page_name} (ID: {page_id}). Bỏ qua.", logging.WARNING)
                    continue
                
                page_token = self.page_tokens[page_id].access_token
                FacebookAdsApi.init(access_token=page_token)
                
                posts = self.get_all_posts(page_id, since_date, until_date)
                
                for post in posts:
                    post_id = post['id']
                    try:
                        insights = self.get_post_insights(page_id, post_id, metrics, since_date, until_date)
                        all_insights.append({
                            'page_id': page_id,
                            'page_name': page_name,
                            'post_id': post_id,
                            'message': post.get('message', ''),
                            'created_time': post.get('created_time'),
                            'permalink_url': post.get('permalink_url', ''),
                            'post_type': post.get('determined_type', 'unknown'),
                            'insights': insights
                        })
                    except Exception as e:
                        custom_logger(f"Lỗi khi lấy insights cho bài đăng {post_id} của trang {page_name}: {str(e)}", logging.ERROR)
            
            return all_insights
        except FacebookRequestError as e:
            custom_logger(f"FacebookRequestError: {str(e)}", logging.ERROR)
            raise Exception(f"Lỗi khi lấy insights của business: {str(e)}")
        except Exception as e:
            custom_logger(f"Unexpected error: {str(e)}", logging.ERROR)
            raise
        
    def get_all_posts(self, page_id: str, since_date: str, until_date: str):
        all_posts = []
        params = {
            'fields': 'id,message,created_time,permalink_url,attachments{type,media_type,title,description,url},status_type',
            'since': since_date,
            'until': until_date,
            'limit': 100
        }
        
        try:
            page = Page(page_id)
            posts = page.get_posts(params=params)
            custom_logger(f"Retrieved post {posts} ", logging.INFO)
            while True:
                for post in posts:
                    post_data = post.export_all_data()
                    post_type = self.determine_post_type(post_data)
                    post_data['determined_type'] = post_type

                    all_posts.append(post_data)
                
                # Kiểm tra xem có trang tiếp theo không
                if 'paging' in posts and 'next' in posts['paging']:
                    next_url = posts['paging']['next']
                    posts = self.api.get_object(next_url)
                else:
                    break
        except Exception as e:
            custom_logger(f"Lỗi khi lấy bài đăng cho trang {page_id}: {str(e)}", logging.ERROR)
        
        return all_posts

    def determine_post_type(self, post_data):
        if 'attachments' in post_data and 'data' in post_data['attachments']:
            attachment = post_data['attachments']['data'][0]
            attachment_type = attachment.get('type')
            media_type = attachment.get('media_type')
            
            if attachment_type == 'share':
                return 'link'
            elif attachment_type == 'photo':
                return 'photo'
            elif attachment_type == 'video' or media_type == 'video':
                return 'video'
            elif attachment_type == 'album':
                return 'album'
        
        if 'status_type' in post_data:
            if post_data['status_type'] == 'mobile_status_update':
                return 'status'
        
        return 'unknown'

    def get_and_store_page_tokens(self, business_id: str):
        try:
            FacebookAdsApi.init(access_token=self.access_token)
            business = Business(business_id)
            pages = business.get_owned_pages(fields=['id', 'name', 'access_token'])
            
            for page in pages:
                page_data = page.export_all_data()
                page_id = page_data['id']
                page_name = page_data['name']
                page_token = page_data.get('access_token')

                if page_id not in self.page_tokens or not self.page_tokens[page_id].access_token:
                    if page_token:
                        self.page_tokens[page_id] = PageToken(
                            page_id=page_id,
                            page_name=page_name,
                            access_token=page_token,
                            last_updated=datetime.now().isoformat()
                        )
                    else:
                        print(f"Không thể lấy token cho trang {page_name} (ID: {page_id})")

            self.save_page_tokens()
            return self.page_tokens
        except FacebookRequestError as e:
            raise Exception(f"Không thể lấy token trang: {str(e)}")

    def get_long_lived_user_token(self, short_lived_token):
        try:
            url = f"https://graph.facebook.com/{self.api_version}/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": short_lived_token
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data['access_token']
        except Exception as e:
            raise Exception(f"Failed to get long-lived user token: {str(e)}")
    
    def check_and_refresh_token(self):
        if self.refresh_attempts >= 3:
            raise Exception("Maximum token refresh attempts reached")

        try:
            # Check token expiration
            url = f"https://graph.facebook.com/{self.api_version}/debug_token"
            params = {
                "input_token": self.access_token,
                "access_token": f"{self.app_id}|{self.app_secret}"
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()['data']

            # If token is expired or will expire soon (e.g., within 24 hours)
            if 'expires_at' in data and data['expires_at']>0 and data['expires_at'] < datetime.now().timestamp() + 86400:
                print("Token is expired or will expire soon. Refreshing...")
                self.refresh_token()
            else:
                print("Token is still valid.")
        except Exception as e:
            print(f"Error checking token: {str(e)}")
            self.refresh_token()

    def refresh_token(self):
        self.refresh_attempts += 1
        try:
            url = f"https://graph.facebook.com/{self.api_version}/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": self.access_token
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            self.access_token = data['access_token']
            self.init_api()  # Reinitialize API with new token
            
            # Update config with new token
            config['access_token'] = self.access_token
            save_config(config)
            
            print("Token refreshed successfully.")
            self.refresh_attempts = 0  # Reset attempts after successful refresh
        except Exception as e:
            print(f"Failed to refresh token (Attempt {self.refresh_attempts}): {str(e)}")
            if self.refresh_attempts < 3:
                print("Retrying...")
                self.check_and_refresh_token()
            else:
                raise Exception("Failed to refresh token after 3 attempts")
            
    def get_post_insights(self, page_id: str, post_id: str, metrics: List[str], since_date: str, until_date: str):
        if page_id not in self.page_tokens:
            raise Exception(f"No access token found for page ID: {page_id}")
        
        token = self.page_tokens[page_id].access_token
        try:
            FacebookAdsApi.init(access_token=token)
            post = Post(post_id)
            fb_metrics = [AVAILABLE_METRICS[m] for m in metrics if m in AVAILABLE_METRICS]
            
            insights = post.get_insights(
                params={
                    "metric": fb_metrics,
                    "since": since_date,
                    "until": until_date,
                }
            )
            
            processed_insights = []
            for insight in insights:
                insight_data = insight.export_all_data()
                processed_insight = {
                    "name": insight_data['name'],
                    "period": insight_data['period'],
                    "values": []
                }
                
                for value in insight_data['values']:
                    processed_value = {}
                    for key, val in value.items():
                        if isinstance(val, (dict, list)):
                            if isinstance(val, dict):
                                processed_value[key] = sum(val.values())
                            else:  # list
                                processed_value[key] = sum(val)
                        else:
                            processed_value[key] = val
                    processed_insight['values'].append(processed_value)
                
                processed_insights.append(processed_insight)
            
            return processed_insights
        except FacebookRequestError as e:
            raise Exception(f"Failed to get insights for post {post_id}: {str(e)}")
    def debug_token_detailed(self, token):
        try:
            url = f"https://graph.facebook.com/{self.api_version}/debug_token"
            params = {
                "input_token": token,
                "access_token": f"{self.app_id}|{self.app_secret}"
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            raise Exception(f"Failed to debug token: {str(e)}")

    def check_page_access(self, token, page_id):
        try:
            FacebookAdsApi.init(access_token=token)
            page = Page(page_id)
            fields = ['id', 'name']
            page_info = page.api_get(fields=fields)
            return page_info
        except FacebookRequestError as e:
            return {"error": str(e), "error_code": e.api_error_code()}

    def test_insights_access(self, token, page_id):
        try:
            FacebookAdsApi.init(access_token=token)
            page = Page(page_id)
            insights = page.get_insights(params={"metric": ["page_impressions"], "period": "day"})
            return {"success": True, "data": [insight.export_all_data() for insight in insights]}
        except FacebookRequestError as e:
            return {"error": str(e), "error_code": e.api_error_code()}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}

    def check_business_pages_access(self, business_id):
        try:
            FacebookAdsApi.init(access_token=self.access_token)
            business = Business(business_id)
            pages = business.get_owned_pages(fields=['id', 'name', 'access_token'])
            
            results = []
            for page in pages:
                page_data = page.export_all_data()
                page_id = page_data.get('id')
                page_token = self.page_tokens.get(page_id, PageToken(page_id=page_id, page_name=page_data.get('name'), access_token='', last_updated='')).access_token
                if not page_token:
                    page_token = page_data.get('access_token', self.access_token)
                
                page_result = {
                    "id": page_id,
                    "name": page_data.get('name'),
                    "has_access_token": bool(page_token),
                    "insights_access": self.test_insights_access(page_token, page_id)
                }
                results.append(page_result)
            
            return results
        except FacebookRequestError as e:
            return {"error": str(e), "error_code": e.api_error_code()}
        except Exception as e:
            return {"error": f"Đã xảy ra lỗi không mong đợi: {str(e)}"}
    
    def get_video_insights(self, video_id: str, metrics: List[str]):
        try:
            api = FacebookAdsApi.get_default_api()
            url = f"https://graph.facebook.com/{self.api_version}/{video_id}/video_insights"
            
            fb_metrics = [AVAILABLE_REEL_METRICS[m] for m in metrics if m in AVAILABLE_REEL_METRICS]
            if 'post_video_likes_by_reaction_type' not in fb_metrics:
                fb_metrics.append('post_video_likes_by_reaction_type')
            if 'post_video_social_actions' not in fb_metrics:
                fb_metrics.append('post_video_social_actions')
            
            metrics_string = ','.join(set(fb_metrics))
            
            response = api.call('GET', url, params={'metric': metrics_string})
            data = response.json()
            
            custom_logger(f"Video insights data for video {video_id}: {json.dumps(data, indent=2)}", logging.DEBUG)

            insights = {}
            if 'data' in data:
                for insight in data['data']:
                    metric_name = insight.get('name')
                    if metric_name in fb_metrics:
                        values = insight.get('values', [])
                        if values and isinstance(values[0], dict):
                            value = values[0].get('value', '')
                            if metric_name == 'post_video_likes_by_reaction_type':
                                reaction_mapping = {
                                    'REACTION_LIKE': 'like',
                                    'REACTION_LOVE': 'love',
                                    'REACTION_WOW': 'wow',
                                    'REACTION_HAHA': 'haha',
                                    'REACTION_SORRY': 'sorry',
                                    'REACTION_ANGER': 'anger'
                                }
                                 
                                insights['reactions'] = sum(value.values())
                                for reaction_type, reaction_count in value.items():
                                    mapped_reaction = reaction_mapping.get(reaction_type, reaction_type.lower())
                                    insights[mapped_reaction] = reaction_count
                                   
                            elif metric_name == 'post_video_social_actions':
                                insights['reels_total_comment_share'] = sum(value.values()) if isinstance(value, dict) else value
                            else:
                                original_metric = next(key for key, value in AVAILABLE_REEL_METRICS.items() if value == metric_name)
                                insights[original_metric] = value
                        elif values:
                            original_metric = next(key for key, value in AVAILABLE_REEL_METRICS.items() if value == metric_name)
                            insights[original_metric] = values[0]
                        else:
                            original_metric = next(key for key, value in AVAILABLE_REEL_METRICS.items() if value == metric_name)
                            insights[original_metric] = ''

            return insights
        except FacebookRequestError as e:
            custom_logger(f"FacebookRequestError when getting video insights for video {video_id}: {str(e)}", logging.ERROR)
            return {}
        except Exception as e:
            custom_logger(f"Unexpected error when getting video insights for video {video_id}: {str(e)}", logging.ERROR)
            return {}
            
    def get_all_page_videos(self, page_id: str, since_date: str, until_date: str):
        all_videos = []
        params = {
            'fields': 'id,title,description,created_time,updated_time,length,permalink_url',
            'since': since_date,
            'until': until_date,
            'limit': 100
        }
        
        try:
            api = FacebookAdsApi.get_default_api()
            url = f"https://graph.facebook.com/{self.api_version}/{page_id}/video_reels"
            
            while True:
                response = api.call('GET', url, params=params)
                data = response.json()
                
                if 'data' in data:
                    all_videos.extend(data['data'])
                
                if 'paging' in data and 'next' in data['paging']:
                    url = data['paging']['next']
                    params = {}  # Clear params as they are included in the next URL
                else:
                    break
        except Exception as e:
            custom_logger(f"Lỗi khi lấy videos cho trang {page_id}: {str(e)}", logging.ERROR)
        
        return all_videos

    def get_all_business_video_insights(self, business_id: str, metrics: List[str], since_date: str, until_date: str):
        try:
            FacebookAdsApi.init(access_token=self.access_token)
            business = Business(business_id)
            pages = business.get_owned_pages(fields=['id', 'name'])
            
            all_video_insights = []
            for page in pages:
                page_data = page.export_all_data()
                page_id = page_data['id']
                page_name = page_data['name']
                
                if page_id not in self.page_tokens:
                    custom_logger(f"Không có token cho trang {page_name} (ID: {page_id}). Bỏ qua.", logging.WARNING)
                    continue
                
                page_token = self.page_tokens[page_id].access_token
                FacebookAdsApi.init(access_token=page_token)
                
                videos = self.get_all_page_videos(page_id, since_date, until_date)
                for video in videos:
                    video_id = video['id']
                    insights = self.get_video_insights(video_id, metrics)
                    video_data = {
                        'page_id': page_id,
                        'page_name': page_name,
                        'video_id': video_id,
                        'title': video.get('title', ''),
                        'description': video.get('description', ''),
                        'created_time': video.get('created_time'),
                        'updated_time': video.get('updated_time'),
                        'length': video.get('length'),
                        'live_status': video.get('live_status'),
                        'permalink_url': video.get('permalink_url'),
                        'insights': insights
                    }
                    all_video_insights.append(video_data)
            
            return all_video_insights
        except FacebookRequestError as e:
            custom_logger(f"FacebookRequestError: {str(e)}", logging.ERROR)
            raise Exception(f"Lỗi khi lấy video insights của business: {str(e)}")
        except Exception as e:
            custom_logger(f"Unexpected error: {str(e)}", logging.ERROR)
            raise

    def get_all_business_posts_and_reels_insights(self, business_id: str, post_metrics: List[str], reel_metrics: List[str], since_date: str, until_date: str):
        try:
            posts_insights = self.get_all_business_post_insights(business_id, post_metrics, since_date, until_date)
            reels_insights = self.get_all_business_video_insights(business_id, reel_metrics, since_date, until_date)
            
            combined_insights = []
            for post in posts_insights:
                combined_post = {
                    'page_id': post['page_id'],
                    'page_name': post['page_name'],
                    'post_id': post['post_id'],
                    'message': post['message'],
                    'created_time': post['created_time'],
                    'permalink_url': post['permalink_url'],
                    'post_type': 'post',
                    'insights': {}
                }
                for metric in post_metrics:
                    for insight in post['insights']:
                        if insight['name'] == AVAILABLE_METRICS.get(metric, metric):
                            combined_post['insights'][metric] = insight['values'][0]['value']
                            break
                    else:
                        combined_post['insights'][metric] = ''
                combined_insights.append(combined_post)
            
            for reel in reels_insights:
                combined_reel = {
                    'page_id': reel['page_id'],
                    'page_name': reel['page_name'],
                    'post_id': reel['video_id'],
                    'message': reel.get('title', ''),
                    'created_time': reel.get('created_time', ''),
                    'permalink_url': reel.get('permalink_url', ''),
                    'post_type': 'reel',
                    'insights': {}
                }
                for metric in DEFAULT_REEL_METRICS:
                    combined_reel['insights'][metric] = reel['insights'].get(metric, '')
                
                combined_insights.append(combined_reel)
            
            return combined_insights
        except Exception as e:
            custom_logger(f"Error in get_all_business_posts_and_reels_insights: {str(e)}", logging.ERROR)
            raise

    def get_ads_insights(self, ad_account_id: str, metrics: List[str], dimensions: List[str], date_preset: str = 'last_30d', level: str = 'account'):
        try:
            FacebookAdsApi.init(access_token=self.access_token)
            account = AdAccount(f'act_{ad_account_id}')
            
            fields = [ADS_METRICS[m] for m in metrics if m in ADS_METRICS]
            fields += [ADS_DIMENSIONS[d] for d in dimensions if d in ADS_DIMENSIONS]
            
            params = {
                'date_preset': date_preset,
                'level': level,
            }
            
            breakdowns = []
            for d in dimensions:
                if d in ['age', 'gender', 'country', 'region', 'impression_device', 'publisher_platform', 'platform_position', 'device_platform']:
                    breakdowns.append(d)
            
            if breakdowns:
                params['breakdowns'] = breakdowns
            
            insights = account.get_insights(fields=fields, params=params)
            
            return insights
        except FacebookRequestError as e:
            error_message = f"FacebookRequestError: {e.api_error_message()}"
            error_type = e.api_error_type()
            error_code = e.api_error_code()
            custom_logger(f"{error_message}. Type: {error_type}, Code: {error_code}", logging.ERROR)
            raise Exception(f"Failed to get ads insights: {error_message}")
        except Exception as e:
            custom_logger(f"Unexpected error when getting ads insights: {str(e)}", logging.ERROR)
            raise



api_manager = FacebookApiManager(
    app_id=config['app_id'],
    app_secret=config['app_secret'],
    access_token=config['access_token'],
    api_version=config['api_version']
)

app = FastAPI()

@app.get("/refresh_page_tokens")
@app.post("/refresh_page_tokens")
async def refresh_page_tokens(business_id: str = Query(..., description="ID of the business to refresh tokens for")):
    try:
        tokens = api_manager.get_and_store_page_tokens(business_id)
        return {"message": f"Đã làm mới token thành công cho {len(tokens)} trang", "tokens": [{"page_id": k, "page_name": v.page_name} for k, v in tokens.items()]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/refresh_token")
async def refresh_token():
    try:
        api_manager.check_and_refresh_token()
        return {"message": "Token checked and refreshed if necessary", "current_token": api_manager.access_token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/post_insights")
async def get_post_insights(
    page_id: str,
    post_id: str,
    metrics: str = Query(..., description="Comma-separated list of metrics"),
    since_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    until_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    try:
        metrics_list = metrics.split(',')
        invalid_metrics = [m for m in metrics_list if m not in AVAILABLE_METRICS]
        if invalid_metrics:
            raise HTTPException(status_code=400, detail=f"Invalid metrics: {', '.join(invalid_metrics)}")
        
        insights = api_manager.get_post_insights(page_id, post_id, metrics_list, since_date, until_date)
        
        # Chuyển đổi insights thành định dạng dễ đọc hơn
        formatted_insights = []
        for insight in insights:
            formatted_insight = {
                "name": insight['name'],
                "period": insight['period'],
                "values": insight['values']
            }
            formatted_insights.append(formatted_insight)
        
        return {"insights": formatted_insights}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/list_stored_page_tokens")
async def list_stored_page_tokens():
    return {
        "page_tokens": [
            {
                "page_id": token.page_id,
                "page_name": token.page_name,
                "last_updated": token.last_updated
            } for token in api_manager.page_tokens.values()
        ]
    }

@app.get("/debug_token_detailed")
async def debug_token_detailed(token: str = Query(...)):
    try:
        token_info = api_manager.debug_token_detailed(token)
        return {
            "token_info": token_info,
            "scopes": token_info.get('scopes', []),
            "app_id": token_info.get('app_id'),
            "type": token_info.get('type'),
            "application": token_info.get('application'),
            "data_access_expires_at": token_info.get('data_access_expires_at'),
            "expires_at": token_info.get('expires_at')
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/check_page_access")
async def check_page_access(token: str, page_id: str):
    result = api_manager.check_page_access(token, page_id)
    if "error" in result:
        return {"success": False, "error": result["error"], "error_code": result["error_code"]}
    return {"success": True, "page_info": result}

@app.get("/test_insights_access")
async def test_insights_access(token: str, page_id: str):
    result = api_manager.test_insights_access(token, page_id)
    if "error" in result:
        return {"success": False, "error": result["error"], "error_code": result["error_code"]}
    return result

@app.get("/check_business_pages_access")
async def check_business_pages_access(business_id: str):
    results = api_manager.check_business_pages_access(business_id)
    if isinstance(results, dict) and "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])
    return {"pages": results}

@app.get("/available_metrics")
async def get_available_metrics():
    return {"available_metrics": list(AVAILABLE_METRICS.keys())}

@app.get("/available_video_metrics")
async def get_available_video_metrics():
    return {"available_metrics": list(AVAILABLE_REEL_METRICS.keys())}

def insights_to_csv(insights, metrics_list):
    output = StringIO()
    writer = csv.writer(output)
    
    # Viết header
    header = ['Page ID', 'Page Name', 'Post ID', 'Message', 'Created Time', 'Permalink URL', 'Post Type'] + metrics_list
    writer.writerow(header)
    
    # Viết dữ liệu
    for post in insights:
        row = [
            post['page_id'],
            post['page_name'],
            post['post_id'],
            post['message'],
            post['created_time'],
            post['permalink_url'],
            post['post_type']
        ]
        for metric in metrics_list:
            # Tìm giá trị metric trong danh sách insights
            metric_value = ''
            for insight in post['insights']:
                if insight['name'] == AVAILABLE_METRICS.get(metric, metric):
                    values = insight.get('values', [])
                    if values and isinstance(values[0], dict):
                        metric_value = values[0].get('value', '')
                    break
            row.append(metric_value)
        writer.writerow(row)
    
    return output

def combined_insights_to_csv(combined_insights, post_metrics, reel_metrics):
    output = StringIO()
    writer = csv.writer(output)
    
    # Tạo header
    all_metrics = list(set(post_metrics + reel_metrics))
    header = ['Page ID', 'Page Name', 'Post ID', 'Message', 'Created Time', 'Permalink URL', 'Post Type'] + all_metrics
    writer.writerow(header)
    
    # Viết dữ liệu
    for item in combined_insights:
        row = [
            item['page_id'],
            item['page_name'],
            item['post_id'],
            item['message'],
            item['created_time'],
            item['permalink_url'],
            item['post_type']
        ]
        for metric in all_metrics:
            row.append(item['insights'].get(metric, ''))
        writer.writerow(row)
    
    return output

def validate_metrics(metrics: str) -> List[str]:
    metrics_list = metrics.split(',')
    invalid_metrics = [m for m in metrics_list if m not in AVAILABLE_METRICS]
    if invalid_metrics:
        raise HTTPException(status_code=400, detail=f"Invalid metrics: {', '.join(invalid_metrics)}")
    return metrics_list


def validate_reel_metrics(metrics: str) -> List[str]:
    metrics_list = metrics.split(',')
    invalid_metrics = [m for m in metrics_list if m not in AVAILABLE_REEL_METRICS]
    if invalid_metrics:
        raise HTTPException(status_code=400, detail=f"Invalid metrics: {', '.join(invalid_metrics)}")
    return metrics_list


def video_insights_to_csv(video_insights, metrics):
    output = StringIO()
    writer = csv.writer(output)
    
    # Tạo header
    reaction_types = ['like', 'love', 'wow', 'haha', 'sorry', 'anger']
    header = ['Page ID', 'Page Name', 'Video ID', 'Title', 'Description', 'Created Time', 'Updated Time', 'Length', 'Permalink URL']
    header.extend(reaction_types)
    header.extend([m for m in metrics if m not in reaction_types and m != 'reactions'])
    header.append('reactions')
    header.append('engaged_users')
    writer.writerow(header)
    
    # Viết dữ liệu
    for video in video_insights:
        row = [
            video['page_id'],
            video['page_name'],
            video['video_id'],
            video['title'],
            video['description'],
            video['created_time'],
            video['updated_time'],
            video['length'],
            video['permalink_url']
        ]
        
        for reaction in reaction_types:
            row.append(video['insights'].get(reaction, 0))
        
        for metric in metrics:
            if metric not in reaction_types and metric != 'reactions':
                row.append(video['insights'].get(metric, ''))
        
        row.append(video['insights'].get('reactions', 0))
        # engaged_users
        row.append(video['insights'].get('reactions', 0))

        writer.writerow(row)
    
    return output


def ads_insights_to_csv(insights, fields):
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(fields)
    
    # Write data
    for insight in insights:
        row = []
        for field in fields:
            value = insight.get(ADS_METRICS.get(field) or ADS_DIMENSIONS.get(field), '')
            if isinstance(value, list):
                # For actions and cost_per_action_type
                value = json.dumps(value)
            row.append(value)
        writer.writerow(row)
    
    return output


#http://localhost:8000/business_post_insights_csv?business_id=1602411516748597&since_date=2024-04-20&until_date=2024-07-05&metrics=impressions,reach,engaged_users,reactions,clicks,like,love,wow,haha,sorry,anger,video_views,video_avg_time_watched,video_length,link_clicks,negative_feedback
@app.get("/business_post_insights_csv")
async def get_business_post_insights_csv(
    business_id: str = Query(..., description="ID of the business"),
    metrics: str = Query("impressions,reach,engaged_users,reactions,clicks,like,love,wow,haha,sorry,anger,video_views,video_avg_time_watched,video_length,link_clicks,negative_feedback", description="Comma-separated list of metrics"),
    since_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    until_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    try:
        custom_logger(f"Received request for business_id: {business_id}, metrics: {metrics}, since: {since_date}, until: {until_date}", logging.DEBUG)
        
        metrics_list = validate_metrics(metrics)
        
        custom_logger("Calling get_all_business_post_insights", logging.DEBUG)
        insights = api_manager.get_all_business_post_insights(business_id, metrics_list, since_date, until_date)
        
        custom_logger(f"Received insights for {len(insights)} posts", logging.DEBUG)
        
        # Chuyển đổi insights thành CSV
        csv_data = insights_to_csv(insights, metrics_list)
        
        # Tạo một response có thể stream
        response = StreamingResponse(iter([csv_data.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=business_post_insights_{business_id}.csv"
        
        return response
    
    except HTTPException as he:
        raise he
    except Exception as e:
        custom_logger(f"Error in get_business_post_insights_csv: {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=str(e))

#http://localhost:8000/business_video_insights_csv?business_id=1602411516748597&since_date=2024-04-20&until_date=2024-07-05&metrics=total_video_views,total_video_impressions
@app.get("/business_video_insights_csv")
async def get_business_video_insights_csv(
    business_id: str = Query(..., description="ID of the business"),
    metrics: str = Query(None, description="Comma-separated list of metrics"),
    since_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    until_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    try:
        custom_logger(f"Received request for business video insights. Business ID: {business_id}, metrics: {metrics}, since: {since_date}, until: {until_date}", logging.INFO)
        
        if metrics is None:
            metrics_list = DEFAULT_REEL_METRICS
        else:
            metrics_list = validate_reel_metrics(metrics)

            # Kiểm tra xem các metrics được yêu cầu có hợp lệ không
            invalid_metrics = [m for m in metrics_list if m not in AVAILABLE_REEL_METRICS]
            if invalid_metrics:
                raise HTTPException(status_code=400, detail=f"Invalid metrics: {', '.join(invalid_metrics)}")
        
        video_insights = api_manager.get_all_business_video_insights(business_id, metrics_list, since_date, until_date)
        
        custom_logger(f"Retrieved insights for {len(video_insights)} videos", logging.INFO)
        
        if not video_insights:
            custom_logger("No video insights received, returning empty CSV", logging.WARNING)
            return StreamingResponse(iter([""]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=empty_business_video_insights_{business_id}.csv"})
        
        csv_data = video_insights_to_csv(video_insights, metrics_list)
        
        response = StreamingResponse(iter([csv_data.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=business_video_insights_{business_id}.csv"
        
        return response
    
    except HTTPException as he:
        raise he
    except Exception as e:
        custom_logger(f"Error in get_business_video_insights_csv: {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/business_posts_and_reels_insights_csv")
async def get_business_posts_and_reels_insights_csv(
    business_id: str = Query(..., description="ID of the business"),
    post_metrics: str = Query("impressions,reach,engaged_users,reactions,clicks,like,love,wow,haha,sorry,anger,link_clicks,negative_feedback", description="Comma-separated list of post metrics"),
    reel_metrics: str = Query(",".join(DEFAULT_REEL_METRICS), description="Comma-separated list of reel metrics"),
    since_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    until_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    try:
        custom_logger(f"Received request for business_id: {business_id}, post_metrics: {post_metrics}, reel_metrics: {reel_metrics}, since: {since_date}, until: {until_date}", logging.DEBUG)
        
        post_metrics_list = validate_metrics(post_metrics)
        reel_metrics_list = validate_reel_metrics(reel_metrics)
        
        combined_insights = api_manager.get_all_business_posts_and_reels_insights(
            business_id, post_metrics_list, reel_metrics_list, since_date, until_date
        )
        
        custom_logger(f"Retrieved combined insights for {len(combined_insights)} items", logging.DEBUG)
        
        if not combined_insights:
            custom_logger("No insights received, returning empty CSV", logging.WARNING)
            return StreamingResponse(iter([""]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=empty_business_posts_and_reels_insights_{business_id}.csv"})
        
        csv_data = combined_insights_to_csv(combined_insights, post_metrics_list, reel_metrics_list)
        
        response = StreamingResponse(iter([csv_data.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=business_posts_and_reels_insights_{business_id}.csv"
        
        return response
    
    except HTTPException as he:
        raise he
    except Exception as e:
        custom_logger(f"Error in get_business_posts_and_reels_insights_csv: {str(e)}", logging.ERROR)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/available_ads_metrics")
async def get_available_ads_metrics():
    return {"available_metrics": list(ADS_METRICS.keys())}

@app.get("/ads_insights")
async def get_ads_insights(
    ad_account_id: str = Query(..., description="ID of the ad account"),
    metrics: str = Query(..., description="Comma-separated list of metrics"),
    dimensions: str = Query("campaign_name,adset_name,ad_name", description="Comma-separated list of dimensions"),
    date_preset: str = Query('last_30d', description="Date preset for the report"),
    level: str = Query('ad', description="Level of reporting (account, campaign, adset, ad)")
):
    try:
        metrics_list = metrics.split(',')
        dimensions_list = dimensions.split(',') if dimensions else []
        
        invalid_metrics = [m for m in metrics_list if m not in ADS_METRICS]
        if invalid_metrics:
            raise HTTPException(status_code=400, detail=f"Invalid metrics: {', '.join(invalid_metrics)}")
        
        invalid_dimensions = [d for d in dimensions_list if d not in ADS_DIMENSIONS]
        if invalid_dimensions:
            raise HTTPException(status_code=400, detail=f"Invalid dimensions: {', '.join(invalid_dimensions)}")
        
        insights = api_manager.get_ads_insights(ad_account_id, metrics_list, dimensions_list, date_preset, level)
        
        # Convert insights to a more readable format
        formatted_insights = []
        for insight in insights:
            formatted_insight = {}
            for field in insight:
                if field == 'actions' or field == 'cost_per_action_type':
                    formatted_insight[field] = [{action['action_type']: action['value']} for action in insight[field]]
                else:
                    formatted_insight[field] = insight[field]
            formatted_insights.append(formatted_insight)
        
        return {"insights": formatted_insights}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# http://127.0.0.1:8000/ads_insights_csv?ad_account_id=142220018771186&dimensions=campaign_name&metrics=impressions,reach,clicks,ctr,cpc,cpm,spend,conversions,cost_per_action_type,purchase_roas
@app.get("/ads_insights_csv")
async def get_ads_insights_csv(
    ad_account_id: str = Query(..., description="ID of the ad account"),
    metrics: str = Query(..., description="Comma-separated list of metrics"),
    dimensions: str = Query("campaign_name,adset_name,ad_name", description="Comma-separated list of dimensions"),
    date_preset: str = Query('last_30d', description="Date preset for the report"),
    level: str = Query('ad', description="Level of reporting (account, campaign, adset, ad)")
):
    try:
        metrics_list = metrics.split(',')
        dimensions_list = dimensions.split(',') if dimensions else []
        
        invalid_metrics = [m for m in metrics_list if m not in ADS_METRICS]
        if invalid_metrics:
            raise HTTPException(status_code=400, detail=f"Invalid metrics: {', '.join(invalid_metrics)}")
        
        invalid_dimensions = [d for d in dimensions_list if d not in ADS_DIMENSIONS]
        if invalid_dimensions:
            raise HTTPException(status_code=400, detail=f"Invalid dimensions: {', '.join(invalid_dimensions)}")
        
        insights = api_manager.get_ads_insights(ad_account_id, metrics_list, dimensions_list, date_preset, level)
        
        csv_data = ads_insights_to_csv(insights, dimensions_list + metrics_list)
        
        response = StreamingResponse(iter([csv_data.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=ads_insights_{ad_account_id}.csv"
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/available_ads_dimensions")
async def get_available_ads_dimensions():
    return {"available_dimensions": list(ADS_DIMENSIONS.keys())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
