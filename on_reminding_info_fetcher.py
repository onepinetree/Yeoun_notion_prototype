import random
from notion_info_fetcher import NotionInfoFetcher
from on_reminding_tag_modifier import OnRemindingTagModifier





class OnRemindingInfoFetcher(NotionInfoFetcher):
    '''인스턴스를 생성하면 복기 할 책에 대한 정보가 생성되고 메소드를 통해 복기를 진행할 수 있는 클래스'''

    def __init__(self, notion_api_key, page_link):
        super().__init__(notion_api_key, page_link)
        self.on_remind_book_dict = self.getOnRemindingBookDict()  # 복기 활성화 상태의 책 이름과 그 책의 페이지ID로 이루어진 dict {책 이름 : 책 pageID, ...}

        if not self.on_remind_book_dict:
            # 복기 활성화 책이 없을 경우
            self.now_remind_book_name = ''
            self.now_remind_line = '복기 할 책이 없습니다'
        else:
            self.now_remind_book = self.getOnRemindBookInfo()  # 인스턴스를 만들었을 때의 복기 책 정보 {책 이름 : 책 pageID}
            self.now_remind_book_name = list(self.now_remind_book.keys())[0]  # 인스턴스를 만들었을 때의 복기 책 이름
            self.now_remind_book_pageID = list(self.now_remind_book.values())[0]  # 인스턴스를 만들었을 때의 복기 책 pageID

            # 페이지 정보를 미리 가져와서 캐시에 저장
            self.get_page_info(self.now_remind_book_pageID)
            self.now_remind_book_children_text_block_list = self.get_list_of_children_block(self.now_remind_book_pageID)  # 복기할 책의 자식 블록들
 
            self.tag_modifier = OnRemindingTagModifier(
                notion_api_key=notion_api_key,
                page_link=page_link,
                chosen_book_page_id=self.now_remind_book_pageID
            )
            self.page_remind_index = self.get_page_remind_index()  # 복기 index를 미리 가져와서 저장
            self.now_remind_line = self.get_remind_line()  # 인스턴스를 만들었을 때 결정된 복기 책에서 다음 복기 구절을 가져옴

    def getOnRemindingBookDict(self) -> dict:
        '''복기 활성화 상태의 책 이름과 그 책의 페이지ID로 이루어진 dict {책 이름 : pageID, ...}를 반환하는 함수,
        없으면 빈 dict을 return 하는 함수'''
        onReminding_dict = {}
        for book_json in self.book_database_json:
            tag_object_list = book_json.get('properties', {}).get('복기 태그', {}).get('multi_select', [])
            reminder_tag_list = [tag_object.get('name') for tag_object in tag_object_list]
            if '복기 활성화' in reminder_tag_list:
                book_name = self.getBookName(book_json=book_json)
                onReminding_dict[book_name] = self.book_page_id_dict.get(book_name)
        return onReminding_dict

    def getOnRemindBookInfo(self) -> dict:
        '''인스턴스를 만들었을 때의 복기 책 정보를 {책 이름 : 책 pageID}의 dict으로 반환하는 함수, 
        현재 복기 중인 책이 없으면 빈 dict을 return'''
        if not self.on_remind_book_dict:
            return {}
        random_key = random.choice(list(self.on_remind_book_dict.keys()))
        return {random_key: self.on_remind_book_dict[random_key]}

    def get_page_remind_index(self) -> str:
        '''인스턴스를 만들었을 때의 복기 책의 '복기 index'를 가져옵니다.'''
        page_info = self.get_page_info(self.now_remind_book_pageID)
        if page_info:
            try:
                return page_info['properties'].get('복기 index', {}).get('rich_text', [])[0].get('text', {}).get('content', '')
            except (IndexError, AttributeError, TypeError):
                return None
        else:
            return None

    def get_now_remind_block_json(self) -> dict:
        '''복기할 책 페이지의 child를 하나씩 보면서 현재 index 다음의 json을 가져옵니다. 책이 없거나 골라진 책의 구절이 없으면 return None'''
        if not hasattr(self, 'now_remind_book_children_text_block_list'): #책이 없을 경우: None을 반환
            return None

        now_remind_book_children_text_block_list = self.now_remind_book_children_text_block_list
        index_found = False
        if not self.page_remind_index:
            # 복기 index가 없을 경우: 첫 번째 블록을 반환
            # 책에 구절이 없을 경우:  None을 반환
            next_block = now_remind_book_children_text_block_list[0] if now_remind_book_children_text_block_list else None
            if next_block:
                self.tag_modifier.update_remind_index_after_reminder(update_index=next_block.get('id'))
            return next_block

        for idx, child_json in enumerate(now_remind_book_children_text_block_list):
            if index_found:
                # 현재 index 다음의 블록을 반환
                self.tag_modifier.update_remind_index_after_reminder(update_index=child_json.get('id'))
                if idx == len(now_remind_book_children_text_block_list) - 1:
                    # 마지막 블록이라면 복기 활성화 태그를 제거
                    self.tag_modifier.update_page_tags_after_reminder()
                return child_json
            if child_json.get('id') == self.page_remind_index:
                index_found = True

        # 현재 index를 찾지 못한 경우
        self.tag_modifier.update_page_tags_after_reminder()
        return None

    def get_remind_line(self) -> str:
        '''복기 책 구절과 그 책의 이름을 반환하는 함수'''
        try:
            indexed_block_json = self.get_now_remind_block_json()
            main_phrase = self.getTextFromBlock(block_json=indexed_block_json)

            if not indexed_block_json or not main_phrase: # 복기 구절이 없을 때
                raise ValueError

            if indexed_block_json.get('has_children', False):
                child_blocks = self.get_list_of_children_block(block_id=indexed_block_json.get('id'))
                if child_blocks:
                    for child_block_json in child_blocks:
                        text = self.getTextFromBlock(child_block_json)
                        if text:
                            main_phrase += '\n' + text
        except:
            self.tag_modifier.update_page_tags_after_reminder()
            main_phrase = '해당 책에 복기할 구절이 없어요. \'복기 태그 없음\'으로 해당 책의 태그를 이동하였어요'

        return main_phrase

    




