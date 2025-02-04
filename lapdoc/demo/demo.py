from pathlib import Path
import pathlib
from lapdoc.verbalizer import LayoutUnawareVerbalizer, SpatialFormatVerbalizer, SpatialFormatYVerbalizer, BoundingBoxMarkupVerbalizer, DescriptiveBoundingBoxVerbalizer, CenterPointVerbalizer
from lapdoc import OCRBox

def read_sroie_sample(id: str):
    cur = Path(__file__).parent.resolve()
    f = cur / 'ICDAR-2019-SROIE' / f'{id}.txt'
    lines = f.read_text().splitlines()
    for l in lines:
        elements = l.split(',', maxsplit=8)
        x0, y0, x1, y1, x2, y2, x3, y3, text = tuple(elements)
        yield OCRBox(x0=int(x0),
                     y0=int(y0),
                     x2=int(x2),
                     y2=int(y2),
                     text=text,
                     page_index=0)

verbs = [
    LayoutUnawareVerbalizer, 
    SpatialFormatVerbalizer,
    SpatialFormatYVerbalizer, 
    BoundingBoxMarkupVerbalizer, 
    DescriptiveBoundingBoxVerbalizer, 
    CenterPointVerbalizer
]

def demo(sample_id):
    print(f'SAMPLE: {sample_id}')
    bboxes = list(read_sroie_sample(sample_id))
    for verbalizer in verbs:
        verbalizer_instance = verbalizer()
        verbalization = verbalizer_instance(bboxes)
        print(verbalizer.__name__)
        print(verbalization)
        print(f'\n\n\n')


demo('X51008142068')
demo('X51008145450')