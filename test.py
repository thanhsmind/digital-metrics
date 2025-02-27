def get_page_reels(self, page_id: str, since_date: str, until_date: str):
    all_reels = []
    params = {
        'fields': 'id,message,created_time,permalink_url,reel_media_duration,reel_playback_duration,reel_audio_title,reel_audio_source,is_instagram_eligible,instagram_eligibility_error_code,instagram_eligibility_error_description',
        'since': since_date,
        'until': until_date,
        'limit': 100
    }
    
    try:
        page = Page(page_id)
        posts = page.get_posts(params=params)
        
        while True:
            for post in posts:
                post_data = post.export_all_data()
                if post_data.get('is_instagram_eligible', False):
                    reel_data = {
                        'id': post_data['id'],
                        'message': post_data.get('message', ''),
                        'created_time': post_data.get('created_time'),
                        'permalink_url': post_data.get('permalink_url', ''),
                        'reel_media_duration': post_data.get('reel_media_duration'),
                        'reel_playback_duration': post_data.get('reel_playback_duration'),
                        'reel_audio_title': post_data.get('reel_audio_title'),
                        'reel_audio_source': post_data.get('reel_audio_source')
                    }
                    all_reels.append(reel_data)
            
            if 'paging' in posts and 'next' in posts['paging']:
                next_url = posts['paging']['next']
                posts = self.api.get_object(next_url)
            else:
                break
    except Exception as e:
        custom_logger(f"Lỗi khi lấy Reels cho trang {page_id}: {str(e)}", logging.ERROR)
    
    return all_reels

def get_all_business_reels(self, business_id: str, since_date: str, until_date: str):
    try:
        FacebookAdsApi.init(access_token=self.access_token)
        business = Business(business_id)
        pages = business.get_owned_pages(fields=['id', 'name'])
        
        all_reels = []
        for page in pages:
            page_data = page.export_all_data()
            page_id = page_data['id']
            page_name = page_data['name']
            
            if page_id not in self.page_tokens:
                custom_logger(f"Không có token cho trang {page_name} (ID: {page_id}). Bỏ qua.", logging.WARNING)
                continue
            
            page_token = self.page_tokens[page_id].access_token
            FacebookAdsApi.init(access_token=page_token)
            
            reels = self.get_page_reels(page_id, since_date, until_date)
            for reel in reels:
                reel['page_id'] = page_id
                reel['page_name'] = page_name
            all_reels.extend(reels)
        
        return all_reels
    except FacebookRequestError as e:
        custom_logger(f"FacebookRequestError: {str(e)}", logging.ERROR)
        raise Exception(f"Lỗi khi lấy Reels của business: {str(e)}")
    except Exception as e:
        custom_logger(f"Unexpected error: {str(e)}", logging.ERROR)
        raise