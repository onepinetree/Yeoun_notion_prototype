import requests


class BlockInfoFetcher:

    def __init__(self, block_json) -> None:
        self.block_json = block_json
        self.id = ''

class BookBlockInfoFetcher(BlockInfoFetcher):

    def __init__(self, block_json) -> None:
        super().__init__(block_json)
        self.book_name = self.getBookName()

    def getBookName(self, emoji = True)->str:
        book_title_list = self.block_json.get('properties', '').get('이름', '').get('title', '')
        if len(book_title_list)>0:
            book_name = book_title_list[0].get('text', '').get('content', '')
            book_icon = self.block_json.get('icon', '')
            if book_icon:
                book_icon = book_icon.get('emoji', '')
            return_name = f'{book_icon} {book_name}' if emoji and book_icon else book_name
        else:
            return ''
        return return_name

class NotionInfoFetcher:
    def __init__(self, notion_api_key, page_link):
        self.notion_api_key = notion_api_key
        self.page_link = page_link
        self.headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        # 캐시용 변수 초기화 (Initialize cache variables before method calls)
        self.page_info_cache = {}
        self.block_children_cache = {}
        self.database_id = self.getDatabaseID()
        self.book_database_json = self.getBookDatabase()
        self.book_page_id_dict = self.getBookPageIdDict()
        self.book_page_id_dict_without_emoji = self.getBookPageIdDict(emoji=False)

    @staticmethod
    def getBookId(book_json: dict) -> str:
        return book_json.get('id', '')

    def getBookPageIdDict(self, emoji=True) -> dict:
        '''{책이름 : 페이지ID}의 dict을 return 한다, emoji에 따라 책이름에 이모티콘이 붙는다. 책 이름이 존재하는 것만 포함된다.
        없으면 빈 dict을 return'''
        book_page_id_dict = {}
        for book_json in self.book_database_json:
            book_name = self.getBookName(book_json=book_json, emoji=emoji)
            if book_name:
                book_id = self.getBookId(book_json=book_json)
                book_page_id_dict[book_name] = book_id
        return book_page_id_dict

    def getTextFromBlock(self, block_json):
        '''Block json에서 text가 있으면 그것을 return 하는 함수, 없으면 None을 return '''
        try:
            rich_text = block_json.get('paragraph', {}).get('rich_text', [])
            if rich_text:
                content = rich_text[0].get('text', {}).get('content', '')
                return content if content else None
            else:
                return None
        except Exception:
            return None

    def get_list_of_children_block(self, block_id, text_only=True) -> list:
        '''block(페이지도 블록)에 속해있는 모든 텍스트를 담고 있는 children에 대한 정보를 list로 가지고 옵니다.
        캐싱이 되어있다면 캐싱된걸 가지고 오고 안되어있으면 캐싱을 하고 가지고 옵니다.'''
        if block_id in self.block_children_cache:
            children_data_list = self.block_children_cache[block_id]
        else:
            url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                children_data_list = response.json().get('results')
                # 모든 페이지의 children을 캐싱
                self.block_children_cache[block_id] = children_data_list
            else:
                print(f"Error fetching children: {response.status_code}")
                return None

        if not text_only:
            return children_data_list

        children_text_block = []
        for children_data in children_data_list:
            if self.getTextFromBlock(block_json=children_data):
                children_text_block.append(children_data)
        return children_text_block

    def getDatabaseID(self) -> str: #### <= 실제 페이지 ID를 보고 modifiy 필요하면 다시 해야함
        '''주어진 page_link를 통해 메인 database_id를 구하는 함수, 없으면 ''을 return'''
        page_id = self.page_link.split('/')[-1].split('?')[0].split('-')[-1]
        children_blocks = self.get_list_of_children_block(block_id=page_id, text_only=False)
        if children_blocks:
            for children_block_json in children_blocks:
                if children_block_json.get('type') == 'child_database':
                    return children_block_json.get('id')
        return ''

    def getBookDatabase(self) -> list:
        '''책 메인데이터베이스에 대한 정보를 return 하는 함수, 데이터베이스가 없으면 []을 return'''
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        response = requests.post(url, headers=self.headers)
        if response.status_code == 200:
            return response.json().get('results', [])  # json도 타입은 dict
        else:
            print(f"Error fetching book database: {response.status_code}")
            return []

    @staticmethod
    def getBookName(book_json: dict, emoji=True) -> str:
        '''book_json에서 책 이름을 가지고 옴, emoji를 통해서 이모지를 붙이거나 떌 수 있음, 없으면 ''을 return'''
        book_title_list = book_json.get('properties', {}).get('이름', {}).get('title', [])
        if book_title_list:
            book_name = book_title_list[0].get('text', {}).get('content', '')
            book_icon = book_json.get('icon', {})
            if book_icon:
                book_icon = book_icon.get('emoji', '')
            return f'{book_icon} {book_name}' if emoji and book_icon else book_name
        else:
            return ''

    def get_page_info(self, page_id):
        """호출 처음이면 캐싱을 합니다. 두번쨰부턴 캐싱되어있는 정보를 가지고 옵니다."""
        if page_id in self.page_info_cache:
            return self.page_info_cache[page_id]
        else:
            url = f"https://api.notion.com/v1/pages/{page_id}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                page_info = response.json()
                self.page_info_cache[page_id] = page_info
                return page_info
            else:
                print(f"페이지 정보 가져오기 실패: {response.status_code}, {response.text}")
                return None