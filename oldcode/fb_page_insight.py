import json
import requests
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.post import Post
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.user import User
from facebook_business.exceptions import FacebookRequestError
from datetime import datetime, timedelta
import csv
import io
import uvicorn

# ... (phần đầu của code giữ nguyên)

class FacebookApiManager:
    # ... (các phương thức khác giữ nguyên)

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

    # ... (các phương thức khác giữ nguyên)

# ... (phần còn lại của code giữ nguyên)

@app.get("/refresh_page_tokens")
@app.post("/refresh_page_tokens")
async def refresh_page_tokens(business_id: str = Query(..., description="ID of the business to refresh tokens for")):
    try:
        tokens = api_manager.get_and_store_page_tokens(business_id)
        return {"message": f"Đã làm mới token thành công cho {len(tokens)} trang", "tokens": [{"page_id": k, "page_name": v.page_name} for k, v in tokens.items()]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ... (phần còn lại của code giữ nguyên)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)