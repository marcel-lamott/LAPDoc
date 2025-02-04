from collections import defaultdict
from typing import Iterable
from lapdoc import OCRBox 
from lapdoc.verbalizer.utils import LineRasterizer, LineRasterizerOptions, normalize_coords
from lapdoc import OCRBox


class Verbalizer:
    def __call__(self, bboxes: Iterable[OCRBox]):
        # group bboxes by page
        page_to_bboxes = defaultdict(list)
        for i, bbox in enumerate(bboxes):
            page_to_bboxes[bbox.page_index].append(bbox)
            
        # Iterate pages
        pages_verbalized: list[str] = []
        for i_page in range(max(page_to_bboxes.keys())+1):
            bboxes_on_page = page_to_bboxes[i_page]
            content = self._verbalize_page(bboxes_on_page)
            pages_verbalized.append(content)

        return '\n'.join(pages_verbalized)
        
    def _verbalize_page(self, bboxes: list[OCRBox]):
        pass


class LayoutUnawareVerbalizer(Verbalizer):
    """
    Only includes text from the OCR results.
    Does not include any layout information.
    """

    def _verbalize_page(self, bboxes: list[OCRBox]):
        if bboxes is None:
            return None
        return '\n'.join([f"{l.text}" for l in bboxes])
    

class _SpatialFormatVerbalizerBase(Verbalizer):
    __line_raster: LineRasterizer = None
    __options: LineRasterizerOptions = None

    def __init__(self, options: LineRasterizerOptions):
        super().__init__()
        self.__options = options

    
    def _verbalize_page(self, bboxes: list[OCRBox]):
        # Initialization
        if self.__line_raster is None:
            self.__line_raster = LineRasterizer(self.__options)

        if bboxes is None:
            return None
        
        content = self.__line_raster.convert(bboxes)
        if content is None:
            # Fallback: LayoutUnawareVerbalizer
            content = '\n'.join([f"{l.text}" for l in bboxes])

        return content



class SpatialFormatVerbalizer(_SpatialFormatVerbalizerBase):
    """
    Tries to resemble to original document layout via insertion of newlines and whitespaces.
    """

    def __init__(self):
        super().__init__(LineRasterizerOptions(
                spatially_aware_x=True,
                spatially_aware_y=True,
                max_consecutive_empty_lines=4
            ))
        
class SpatialFormatYVerbalizer(_SpatialFormatVerbalizerBase):
    """
    Tries to resemble to original document layout via insertion of newlines.
    """

    def __init__(self):
        super().__init__(LineRasterizerOptions(
                spatially_aware_x=False,
                spatially_aware_y=True,
                max_consecutive_empty_lines=4
            ))


class DescriptiveBoundingBoxVerbalizer(Verbalizer):
    def _bbox_to_str(self, bbox: OCRBox):
        return f"left:{round(bbox.x0)} top:{round(bbox.y0)} right:{round(bbox.x2)} bottom:{round(bbox.y2)} text:'{bbox.text}'"

    def _verbalize_page(self, bboxes: list[OCRBox]):
        normalized_bboxes = normalize_coords(bboxes)

        return '\n'.join([f'{self._bbox_to_str(l)}' for l in normalized_bboxes])
    

class BoundingBoxMarkupVerbalizer(Verbalizer):
    """
    Lists the OCRBoxes like: <box left=0, top=0, right=0, bottom=0/>Hallo Welt
    """
    def _bbox_to_str(self, bbox: OCRBox):
        return f"<box left={round(bbox.x0)} top={round(bbox.y0)} right={round(bbox.x2)} bottom={round(bbox.y2)}/>{bbox.text}"

    def _verbalize_page(self, bboxes: list[OCRBox]):
        if bboxes is None:
            return None
        
        normalized_bboxes = normalize_coords(bboxes)

        return '\n'.join([f'{self._bbox_to_str(l)}' for l in normalized_bboxes])
    

class CenterPointVerbalizer(Verbalizer):
    """
    Lists the center point for each bounding box + text, without width and heigth
    """
    def _bbox_to_str(self, bbox: OCRBox):
        center_x = round(bbox.x0 + bbox.width / 2)
        center_y = round(bbox.y0 + bbox.height / 2)
        return f"<box x={center_x} y={center_y}/>{bbox.text}"

    def _verbalize_page(self, bboxes: list[OCRBox]):
        if bboxes is None:
            return None
        
        normalized_bboxes = normalize_coords(bboxes)

        return '\n'.join([f'{self._bbox_to_str(l)}' for l in normalized_bboxes])
    
    