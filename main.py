from on_reading_info_fetcher import OnReadingInfoFetcher
from on_reminding_info_fetcher import OnRemindingInfoFetcher
from fastapi import FastAPI, Header, HTTPException
import uvicorn
import os

app = FastAPI()



@app.get("/on-read-books")
async def getOnReadingBook(notion_secret_key: str = Header(...), page_link: str = Header(...)) -> dict:
    if not notion_secret_key or not page_link:
        raise HTTPException(status_code=400, detail="Missing headers")
    
    fetcher = OnReadingInfoFetcher(notion_api_key=notion_secret_key, page_link=page_link)

    return fetcher.getOnReadingBookDict()


@app.get("/remind-line")
async def getRemindLine(notion_secret_key: str = Header(...), page_link: str = Header(...)) -> dict:
    if not notion_secret_key or not page_link:
        raise HTTPException(status_code=400, detail="Missing headers")
    
    fetcher = OnRemindingInfoFetcher(notion_api_key=notion_secret_key, page_link=page_link)

    return {'book_name' : fetcher.now_remind_book_name, 'now_remind_line' : fetcher.now_remind_line}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))



















        