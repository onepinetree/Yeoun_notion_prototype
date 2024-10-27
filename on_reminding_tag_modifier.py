from notion_info_fetcher import NotionInfoFetcher
import requests, json


class OnRemindingTagModifier(NotionInfoFetcher):
    '''복기하기로 결정된 책의 iD를 넣어 생성하면 update_page_tags_after_reminder함수를 통해 복기 태그를 없앨 수 있음'''

    def __init__(self, notion_api_key, page_link, chosen_book_page_id):
        super().__init__(notion_api_key, page_link)
        self.chosen_book_page_id = chosen_book_page_id

    def get_page_tags(self) -> list:
        """페이지의 현재 '복기 태그' 속성을 가져옵니다. 현재 복기 중인 책이 없으면 빈 list를 return"""
        page_info = self.get_page_info(self.chosen_book_page_id)
        if page_info:
            tags_property = page_info['properties'].get('복기 태그', {})
            if tags_property.get('type') == 'multi_select':
                return [tag['name'] for tag in tags_property.get('multi_select', [])]
            else:
                print("'복기 태그' 속성이 'multi_select' 타입이 아닙니다.")
                return []
        else:
            return []

    @staticmethod
    def modify_tags(existing_tags: list) -> list:
        """기존 태그를 기반으로 '복기 활성화'가 있다면 제거합니다."""
        return [tag for tag in existing_tags if tag != '복기 활성화']

    def update_page_tags_after_reminder(self):
        """페이지의 '복기 태그' 속성에서 '복기 활성화'를 제거하고 '복기 index'를 초기화합니다."""
        url = f"https://api.notion.com/v1/pages/{self.chosen_book_page_id}"

        current_tags = self.get_page_tags()
        updated_tags = self.modify_tags(current_tags)
        data = {
            "properties": {
                "복기 태그": {
                    "multi_select": [
                        {"name": tag} for tag in updated_tags
                    ]
                },
                "복기 index": {
                    "rich_text": [
                        {
                            "text": {
                                "content": ""
                            }
                        }
                    ]
                }
            }
        }

        response = requests.patch(url, headers=self.headers, json=data)
        if response.status_code == 200:
            print("페이지의 태그가 성공적으로 업데이트되었습니다.")
        else:
            try:
                error_message = response.json()
                print(f"태그 업데이트 실패: {response.status_code}, 오류 메시지: {error_message}")
            except json.JSONDecodeError:
                print(f"태그 업데이트 실패: {response.status_code}, 응답 내용: {response.text}")

    def update_remind_index_after_reminder(self, update_index: str):
        """페이지의 복기 index를 update합니다."""
        url = f"https://api.notion.com/v1/pages/{self.chosen_book_page_id}"
        data = {
            "properties": {
                "복기 index": {
                    "rich_text": [
                        {"text": {"content": update_index}}
                    ]
                }
            }
        }
        response = requests.patch(url, headers=self.headers, json=data)
        if response.status_code == 200:
            print("페이지의 복기 index가 업데이트되었습니다.")
        else:
            print(f"복기 index 업데이트 실패: {response.status_code}")