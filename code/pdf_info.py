'''
pdf_info is to get the basic infomation from pdfs
info={
filename, height, width, page_no, figure_est_no, layout_bbox, text_mask
}
'''
# from selenium import webdriver
import json
from pathlib import Path
import fitz

def pdf_info_from_fitz(pdf_path, page_output_dir):
    doc = fitz.open(pdf_path)
    info = {
        "filename": Path(pdf_path).name,
        "page_no": doc.page_count,
        "fig_no_est": 0,
    }
    html_info = []
    output_dir = Path(page_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for page_index in range(doc.page_count):
        page = doc[page_index]
        page_num = page_index + 1

        # Render PNG so downstream OpenCV steps still work
        # once the text block coordinates are established (images, drawings, etc are skipped), 
        # then the image block cooridnates will be established
        # using code from this repository (opencv is used to detect figure contours, etc) - then the coordinates 
        # will be used to extract the images from the page pixmap that is saved here.
        # So in short it is neccessary to save the images of the pdf pages for processing.
        pix = page.get_pixmap()
        png_path = output_dir / f"page{page_num}.png"
        pix.save(str(png_path))

        # Collect text blocks
        blocks = []
        for x0, y0, x1, y1, text, block_no, block_type in page.get_text("blocks"):
            if block_type != 0:  # ignore images/drawings; keep only text blocks
                continue
            text = text.strip()
            if not text:
                continue

            # scale_x = pix.width / page.rect.width
            # scale_y = pix.height / page.rect.height
            
            bbox = [x0, y0, x1 - x0, y1 - y0]
            # pixel_bbox = [
            #     int((bbox[0][0]) * scale_x),
            #     int((bbox[0][1]) * scale_y),
            #     int((bbox[0][0] + bbox[0][2]) * scale_x),
            #     int((bbox[0][1] + bbox[0][3]) * scale_y),
            # ]
            blocks.append([bbox, text])

        html_info.append([page_num, blocks, (page.rect.height, page.rect.width)])

    info["page_height"] = doc[0].rect.height
    info["page_width"] = doc[0].rect.width
    info["mess_up"] = False
    info["graph_layout"] = (0, info["page_height"])  # placeholder until you recompute

    json_path = output_dir / f"{info['filename'][:-4]}.json"
    with open(json_path, "w") as fh:
        json.dump(html_info, fh)

    doc.close()
    return info, html_info

    # Column width, middle gap, Maximum Figure number will be helpful
def pdf_info(html_file_path, pdf):
    # Get the pdf info by parsing html

    html_dir = Path(html_file_path)
    # html_dir.mkdir(parents=True, exist_ok=True)

    info = {}
    html_info = []

    json_path = html_dir / f"{pdf[:-4]}.json"
    png_pages = sorted(p.name for p in html_dir.glob("page*.png"))

    if json_path.exists():
        with json_path.open() as json_data:
            html_info = json.load(json_data)

    if not html_info or not png_pages:
        info, html_info = pdf_info_from_fitz(pdf, str(html_dir))
        png_pages = [f"page{page_num}.png" for page_num in range(1, info["page_no"] + 1)]

    if not info:
        info = {"filename": pdf}

    info['filename'] = pdf
    page_no = len(png_pages) if png_pages else info.get('page_no', len(html_info))
    info['page_no'] = page_no

    row_width = []
    row_height = []
    column_no = 1
    columns = [0]
    left_point = []
    top_point = []
    right_point = []

    if html_info:
        first_page_size = html_info[0][2]
        info.setdefault('page_height', first_page_size[0])
        info.setdefault('page_width', first_page_size[1])

    if page_no > 3:
        list_to_check = range(2, page_no)
    else:
        list_to_check = range(1, page_no+1)
    for each_page_html in html_info:
        if each_page_html[0] in list_to_check:
            #print each_page_html[0]
# Obtain page convas region
            info['page_height'] = each_page_html[2][0]
            info['page_width'] = each_page_html[2][1]
            for element in each_page_html[1]:
                # element[1] - is the text data - is no. of words > 30 --> collect the dimensions of the text block (w, h, etc)
                if len(element[1]) > 30:
                    row_width.append(element[0][2])
                    row_height.append(element[0][3])
                    left_point.append(element[0][0])
                    right_point.append(element[0][0]+element[0][2])
                    top_point.append(element[0][1])
    point_left = sorted([(i, left_point.count(i)) for i in set(
        left_point)], key=lambda x: x[1], reverse=True)
    width_row = sorted([(i, row_width.count(i)) for i in set(
        row_width)], key=lambda x: x[1], reverse=True)
    height_row = sorted([(i, row_height.count(i)) for i in set(
        row_height)], key=lambda x: x[1], reverse=True)
    info['row_height'] = height_row[0][0]
    info['row_width'] = width_row[0][0]
    info['text_layout'] = (max(0, min(top_point)),
                           min(info['page_height'],max(top_point)))     # layout of columns - 1 or 2 columns page etc 

    # Compute column no and position for each column
    i = 0
    while i < len(point_left):
        j = i + 1
        while j < len(point_left):
            if abs(point_left[i][0] - point_left[j][0]) <= 10:
                point_left[i] = (point_left[i][0], point_left[i][1] +
                                 point_left[j][1])
                del point_left[j]
            else:
                j = j + 1
        i = i + 1
    point_left = sorted(point_left, key=lambda x: x[1], reverse=True)

    if float(point_left[0][1]) / len(left_point) > 0.75 \
            or float(info['row_width']) / info['page_width'] > 0.5:
        column_no = 1
        columns = [point_left[0][0]]
    else:  # float(point_left[1][1]) / len(left_point) > 0.2:  # Need to
        # correct, it may cause numbe below 0
        column_no = 2  # int(float((info['page_width'] - 2*point_left[0][0]))/info['row_width'])

        for i in range(1, len(point_left)):
            if abs(point_left[i][0] - point_left[0][0]) > info['row_width']:
                columns = [min(point_left[i][0], point_left[0][0]),
                           max(point_left[i][0], point_left[0][0])]
                break

    info['column_no'] = column_no
    info['columns'] = columns

    left_bar = min(left_point)
    right_bar = max(right_point)
    # pdf layout
    if left_bar > 0 and left_bar < 20 * info['row_height']:
        info['left_bbox'] = [0, 0, left_bar, info['page_height']]
        info['right_bbox'] = [min(info['page_width'] - 2 * info['row_height'],right_bar),
                              0, info['page_width'] - min(info['page_width'] - 2 * info['row_height'],right_bar), info['page_height']]
        if info['text_layout'][0] < 15 * info['row_height'] and info['text_layout'][1] > 15 * info['row_height']:
            info['top_bbox'] = [0, 0, info['page_width'], info['text_layout'][0]]
            info['down_bbox'] = [0, info['text_layout'][1], info['page_width'],
                                 info['page_height'] - info['text_layout'][1]]
        else:
            info['top_bbox'] = [0, 0, info['page_width'], info['row_height']]
            info['down_bbox'] = [0, info['page_height'] - info['row_height'], info['page_width'],
                                 info['row_height']]
    else:
        info['left_bbox'] = [0, 0, info['row_height'], info['page_height']]
        info['right_bbox'] = [info['page_width'] - info['row_height'], 0, info['row_height'], info['page_height']]
        info['top_bbox'] = [0, 0, info['page_width'], info['row_height']]
        info['down_bbox'] = [0, info['page_height'] - info['row_height'], info['page_width'], info['row_height']]

    #print info['left_bbox']
    #print info['right_bbox']
    #print info['top_bbox']
    #print info['down_bbox']
    info['mess_up'] = False
    info['graph_layout'] = info['text_layout']

    return info, html_info
'''
           

    
        page_layout = browser.find_element_by_xpath("/html/body/img")
        info['page_height'] = page_layout.size['height']
        info['page_width'] = page_layout.size['width']

        text_elements = browser.find_elements_by_xpath("/html/body/div")
        for element in text_elements:
            if len(element.text) > 30:
                row_width.append(element.size['width'])
                row_height.append(element.size['height'])
                left_point.append(element.location['x'])
                top_point.append(element.location['y'])

    point_left = sorted([(i, left_point.count(i)) for i in set(
            left_point)], key=lambda x: x[1], reverse=True)
    width_row = sorted([(i, row_width.count(i)) for i in set(
            row_width)], key=lambda x: x[1], reverse=True)
    height_row = sorted([(i, row_height.count(i)) for i in set(
            row_height)], key=lambda x: x[1], reverse=True)
    info['row_height'] = height_row[0][0]
    info['row_width'] = width_row[0][0]
    info['text_layout'] = (max(0, min(top_point)),
                               min(info['page_height'],
                                   max(top_point)))
    # Compute column no and position for each column
    i = 0
    while i < len(point_left):
        j = i + 1
        while j < len(point_left):
            if abs(point_left[i][0] - point_left[j][0]) <= 10:
                point_left[i] = (point_left[i][0], point_left[i][1] +
                                     point_left[j][1])
                del point_left[j]
            else:
                j = j + 1
        i = i + 1
    point_left = sorted(point_left, key=lambda x: x[1], reverse=True)

    if float(point_left[0][1]) / len(left_point) > 0.75\
                or float(info['row_width'])/info['page_width'] > 0.5:
        column_no = 1
        columns = [point_left[0][0]]
    else:  # float(point_left[1][1]) / len(left_point) > 0.2:  # Need to
            # correct, it may cause numbe below 0
        column_no = 2 #int(float((info['page_width'] - 2*point_left[0][0]))/info['row_width'])

        for i in range(1, len(point_left)):
            if abs(point_left[i][0] - point_left[0][0]) > info['row_width']:
                columns = [min(point_left[i][0], point_left[0][0]),
                       max(point_left[i][0], point_left[0][0])]
                break

    info['column_no'] = column_no
    info['columns'] = columns

    left_bar = min(left_point)
    # pdf layout
    if left_bar >0 and left_bar < 20*info['row_height']:
        info['left_bbox'] = [0, 0, left_bar, info['page_height']]
        info['right_bbox'] = [info['page_width']-2*info['row_height'],
                              0, 2*info['row_height'], info['page_height']]
        if info['text_layout'][0] < 15*info['row_height'] and info['text_layout'][1] > 15*info['row_height']:
            info['top_bbox'] = [0, 0, info['page_width'], info['text_layout'][0]]
            info['down_bbox'] = [0, info['text_layout'][1], info['page_width'], info['page_height']-info['text_layout'][1]]
        else:
            info['top_bbox'] = [0, 0, info['page_width'], info['row_height']]
            info['down_bbox'] = [0, info['page_height']-info['row_height'], info['page_width'],
                                 info['row_height']]
    else:
        info['left_bbox'] = [0, 0, info['row_height'], info['page_height']]
        info['right_bbox'] = [0, info['page_width'] - info['row_height'], info['row_height'], info['page_height']]
        info['top_bbox'] = [0, 0, info['page_width'], info['row_height']]
        info['down_bbox'] = [0, info['page_height']-info['row_height'], info['page_width'], info['row_height']]

    print info['left_bbox']
    print info['right_bbox']
    print info['top_bbox']
    print info['down_bbox']
    # graph layout
    #
    # if page_no >1:
    #     previous_page = for_counting[list_to_check[0]]
    #     previous_img = cv2.imread(html_file_path + '/' + previous_page)
    #     previous_img = previous_img <240
    #
    #     for page_id in list_to_check[1:]:
    #         page = for_counting[page_id]
    #         img = cv2.imread(html_file_path + '/' + page)
    #         img = img <240
    #         result = img & previous_img
    #         temp_result = result[:, :, 0]
    #         previous_img = result
    #         # xor pages to find the top/bottom line
    #     sum_result = [ sum(each_row) for each_row in temp_result]
    #     sum_result = [i for i in range(len(sum_result)) if sum_result[i] > 0]
    #     top_point = min(sum_result)
    #     bottom_point = max(sum_result)
    #
    #     info['graph_layout'] = info['text_layout']
    # else:ue
    #     info['graph_layout'] = info['text_layout']#(top, down)
    info['mess_up'] = False
    info['graph_layout'] = info['text_layout']
'''



# def read_each_html(x):
#     #browser = webdriver.Chrome('/home/pengyuan/chromedriver')
#     #browser = webdriver.Chrome('/usa/pengyuan/Documents/RESEARCH/PDFigCapX/chromedriver/chromedriver')
#     #browser.implicitly_wait(2)
#     browser.get(x)
#     page_layout = browser.find_element_by_xpath("/html/body/img")
#     img_size = (page_layout.size['height'], page_layout.size['width'])
#     text_elements = browser.find_elements_by_xpath("/html/body/div")
#     text_boxes = []
#     for element in text_elements:
#         text = element.text
#         if len(text) > 0:
#             text_boxes.append([[element.location['x'], element.location['y'], element.size['width'], element.size['height']], text])

#     browser.quit()
#     return int(os.path.basename(x)[4:-5]), text_boxes, img_size
