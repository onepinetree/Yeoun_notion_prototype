from notion_info_fetcher import NotionInfoFetcher


class OnReadingInfoFetcher(NotionInfoFetcher):

    def __init__(self, notion_api_key, page_link):
        super().__init__(notion_api_key, page_link)


    def getOnReadingBookDict(self) -> dict:
        '''읽고 있는 책의 pageID와 이름을 각각 key와 value로 갖고 있는 dict을 return 한다. dict이 비어있으면 ''을 return 한다.'''
        onreading_dict = {}
        for book_json in self.book_database_json:
            read_status = book_json.get('properties', '').get('독서 상태', '').get('status', '').get('name', '')
            if read_status == '읽는 중':
                book_name = self.getBookName(book_json=book_json)
                onreading_dict[book_name] = self.book_page_id_dict.get(book_name)
        if onreading_dict == {}:
            return ''
        return onreading_dict





