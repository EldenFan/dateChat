from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

logging.basicConfig(level=logging.INFO)
'''to do: Сделать, чтобы нажатая клавиша имела обозночение через стикер'''
class Keyboard:
    def __init__(self, items, page_size=5):
        self.items = items
        self.page_size = page_size
        self.total_pages = (len(items) + page_size - 1) // page_size
        logging.info(f"Initialized Keyboard with {len(items)} items and {self.total_pages} pages")

    def get_page(self, current_page=1):
        start_index = (current_page - 1) * self.page_size
        end_index = start_index + self.page_size

        buttons = [
            InlineKeyboardButton(text=item, callback_data=f"trait_{item}")
            for item in self.items[start_index:end_index]
        ]
        logging.info(f"Page {current_page}: Buttons created: {buttons}")

        keyboard = [buttons[i:i+1] for i in range(0, len(buttons), 1)]

        nav_buttons = []
        if self.total_pages > 1:
            if current_page > 1:
                nav_buttons.append(
                    InlineKeyboardButton(text='<< Назад', callback_data=f'page_{current_page-1}')
                )
            if current_page < self.total_pages:
                nav_buttons.append(
                    InlineKeyboardButton(text='Вперед >>', callback_data=f'page_{current_page+1}')
                )

        if nav_buttons:
            keyboard.append(nav_buttons)

        return InlineKeyboardMarkup(inline_keyboard=keyboard)
