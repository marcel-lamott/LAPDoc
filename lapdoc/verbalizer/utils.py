from dataclasses import dataclass
import itertools
import math
from typing import Optional

import numpy as np

from lapdoc import OCRBox


def sort_boxes_by_position(bboxes: list[OCRBox]) -> list[OCRBox]:
    temp = bboxes
    temp = sorted(temp, key=lambda box: box.left + box.width / 2)
    temp = sorted(temp, key=lambda box: box.top + box.height / 2)
    return temp


def remove_duplicates(bboxes: list[OCRBox]):
    return list(dict.fromkeys(bboxes))


def normalize_coords(bboxes: list[OCRBox]) -> list[OCRBox]:
    if not any(bboxes):
        return bboxes
    
    min_x = min(bboxes, key=lambda x: x.x0).x0
    min_y = min(bboxes, key=lambda x: x.y0).y0
 
    new_bboxes: list[OCRBox] = []
    for bbox in bboxes:
        new_bboxes.append(OCRBox(bbox.x0 - min_x, 
                                 bbox.y0 - min_y, 
                                 bbox.x2 - min_x, 
                                 bbox.y2 - min_y, 
                                 bbox.text,
                                 page_index=bbox.page_index))

    return new_bboxes


@dataclass
class LineRasterizerOptions:
    spatially_aware_x: bool
    spatially_aware_y: bool
    max_consecutive_empty_lines: int


class LineRasterizer:
    def __init__(self, options: LineRasterizerOptions):
        self.options = options

    def _is_sample_line(self, box_a: OCRBox, box_b: OCRBox) -> bool:
        mid_a = box_a.top + box_a.height / 2
        mid_b = box_b.top + box_b.height / 2
        mean_box_height = (box_a.height + box_b.height) / 2
        vertical_threshold = mean_box_height / 1.5
        return abs(mid_a - mid_b) <= vertical_threshold

    def determine_line_candidates(self, boxes: list[OCRBox]) -> list[list[OCRBox]]:
        candidates = []
        seen = set()

        def determine_line_candidate(query: OCRBox) -> tuple[set[int], list[OCRBox]]:
            not_seen = set(range(len(boxes))) - seen
            _candidate_idx = {i for i in not_seen if self._is_sample_line(query, boxes[i])}
            _candidate_boxes = [boxes[i] for i in not_seen if self._is_sample_line(query, boxes[i])]
            return _candidate_idx, _candidate_boxes

        for box_idx, box in enumerate(boxes):
            if box_idx in seen:
                continue
            candidate_idx, candidate_boxes = determine_line_candidate(box)
            candidate_boxes = sorted(candidate_boxes, key=lambda c: c.left)
            seen.update(candidate_idx)
            candidates.append(candidate_boxes)

        candidates = [line for line in candidates if len(line) > 0]
        candidates = sorted(candidates, key=lambda line: float(np.mean([b.top for b in line])))
        assert len(boxes) == sum(map(len, candidates))
        return candidates

    def render_line_candidate(self, boxes: list[OCRBox]) -> Optional[OCRBox]:
        if len(boxes) == 0:
            return None

        line_char_width = float(np.median([box.width / len(box.text) for box in boxes]))
        if line_char_width <= 1:
            return None

        # This will disable all horizontal padding instead of word separations.
        use_padding_x = int(self.options.spatially_aware_x)
        n_padding_chars = math.ceil(boxes[0].left / line_char_width) * use_padding_x
        line_str = f'{" " * n_padding_chars}{boxes[0].text}'
        for left_box, right_box in itertools.pairwise(boxes):
            n_padding_chars = math.ceil((right_box.left - left_box.right) / line_char_width) * use_padding_x
            line_str += f'{" " * max(1, n_padding_chars)}{right_box.text}'

        line_box = OCRBox.union_all(boxes, text=line_str)
        return line_box

    def compress_document(self, lines: list[str]) -> list[str]:
        def _remove_leading_empy_lines(board: list[str]) -> list[str]:
            is_empty = [line.strip() == '' for line in board]
            first_non_empty = is_empty.index(False)
            return board[first_non_empty:]

        def _remove_trailing_empy_lines(board: list[str]) -> list[str]:
            return list(reversed(_remove_leading_empy_lines(list(reversed(board)))))

        def _trim_left_padding(board: list[str]) -> list[str]:
            n_padding = [len(line) - len(line.lstrip()) for line in board]
            n_shared_padding = min(n_padding)
            return [line[n_shared_padding:] for line in board]

        compressed = lines
        compressed = _remove_leading_empy_lines(compressed)
        compressed = _remove_trailing_empy_lines(compressed)
        compressed = _trim_left_padding(compressed)
        return compressed

    def render_document(self, line_boxes: list[OCRBox]) -> str:
        if len(line_boxes) == 0:
            return ''

        line_height = float(np.median([line_box.height for line_box in line_boxes])) * 0.9
        # This will disable all vertical padding instead of new lines.
        use_padding_y = int(self.options.spatially_aware_y)

        n_padding_lines = int(line_boxes[0].top / line_height) * use_padding_y
        n_padding_lines = min(n_padding_lines, self.options.max_consecutive_empty_lines)

        lines = []
        lines.extend(["\n"] * n_padding_lines)
        lines.append(line_boxes[0].text + '\n')
        for top_line, bottom_line in itertools.pairwise(line_boxes):
            n_padding_lines = int((bottom_line.top - top_line.bottom) / line_height) * use_padding_y
            n_padding_lines = min(n_padding_lines, self.options.max_consecutive_empty_lines)
            lines.extend(["\n"] * n_padding_lines)
            lines.append(bottom_line.text + '\n')

        lines = self.compress_document(lines)
        return ''.join(lines)

    def convert(self, boxes: list[OCRBox]) -> str:
        boxes = remove_duplicates(boxes)
        boxes = normalize_coords(boxes)
        boxes = sort_boxes_by_position(boxes)
        line_candidates = self.determine_line_candidates(boxes)
        lines = [line for candidate in line_candidates if (line := self.render_line_candidate(candidate))]
        return self.render_document(lines)


