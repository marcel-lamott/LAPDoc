from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OCRBox:
    x0: int
    y0: int
    x2: int
    y2: int
    text: str
    page_index: int

    @property
    def width(self):
        return self.x2 - self.x0

    @property
    def height(self):
        return self.y2 - self.y0

    @property
    def top(self):
        return self.y0

    @property
    def left(self):
        return self.x0

    @property
    def bottom(self):
        return self.y2

    @property
    def right(self):
        return self.x2
    
    @staticmethod
    def union(box_a: OCRBox, box_b: OCRBox, text: Optional[str] = None) -> OCRBox:
        left = min(box_a.left, box_b.left)
        top = min(box_a.top, box_b.top)
        right = max(box_a.right, box_b.right)
        bottom = max(box_a.bottom, box_b.bottom)
        text = text or f'{box_a.text} {box_b.text}'
        return OCRBox(left, top, right, bottom, text, page_index=min(box_a.page_index, box_b.page_index))

    @staticmethod
    def union_all(boxes: list[OCRBox], text: Optional[str] = None) -> Optional[OCRBox]:
        boxes = iter(boxes)
        total = next(boxes, None)
        if not total:
            return None
        for box in boxes:
            total = OCRBox.union(total, box)

        text = text or total.text
        return OCRBox(total.left, total.top, total.right, total.bottom, text, total.page_index)
