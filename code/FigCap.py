"""
main code page
structure (xpdf_process):
1. Read pdfs from input folder
2. Figure and caption pair detection
    2.1. graphical content detection
    2.2 page segmentation
    2.3 figure detetion
    2.4 caption association

3. Mess up pdf processing


Writen by Pengyuan Li

Start from 19/10/2017
1.0 version 28/02/2018

"""

import os
import json
from pprint import pprint
# import renderer
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from xpdf_process import figures_captions_list
import subprocess
import os
import time
from PIL import Image


if __name__ == "__main__":

    input_path = '/home/nmathias/PDFigCapX_mine/input'
    output_path = '/home/nmathias/PDFigCapX_mine/output'
    xpdf_path = output_path +'/xpdf/'  
    log_file = output_path + '/log.text'
    # f_log = open(log_file, 'w') 
    if not os.path.isdir(xpdf_path):
        os.mkdir(xpdf_path)
# Read each files in the input path
    for pdf in os.listdir(input_path):
        if pdf.endswith('.pdf') and (not pdf.startswith('._')):
            data = {}

            pdf_full_path = os.path.join(input_path, pdf)
            basepath = os.path.dirname(pdf_full_path)
            basename = os.path.splitext(os.path.basename(pdf_full_path))[0]
            output_json = os.path.join(basepath, f"{basename}_figures.json")

            print(pdf_full_path)
            # images = renderer.render_pdf(pdf_full_path)
            data[pdf] = {}
            data[pdf]['figures'] = []
            data[pdf]['pages_annotated'] = []
            pdf_flag = 0
            # try:
            #     if not os.path.isdir(xpdf_path+pdf[:-4]):
            #         std_out = subprocess.check_output(["/usa/pengyuan/Documents/RESEARCH/PDFigCapX/xpdf-tools-linux-4.00/bin64/pdftohtml", input_path+'/'+pdf, xpdf_path+pdf[:-4]+'/'])
            # except:
            #     print("\nWrong "+pdf+"\n")
            #     f_log.write(pdf+'\n')
            #     pdf_flag = 1

            if pdf_flag == 0:
                flag = 0
                wrong_count = 0
                info = {'fig_no_est': 0}
                figures = {}
                while flag==0 and wrong_count<5:
                    try:
                        input_path, pdf, output_path
                        figures, info = figures_captions_list(pdf_full_path)
                        flag = 1

                    except Exception as exc:
                        wrong_count = wrong_count +1
                        time.sleep(5)
                        print("Retrying figures_captions_list for {} ({})".format(pdf, exc))
        
                data[pdf]['fig_no'] = info['fig_no_est']

                output_file_path = os.path.join(output_path, pdf[:-4])
                if not os.path.isdir(output_file_path):
                    os.mkdir(output_file_path)      

                page_pngs = {
                    idx + 1: Image.open(os.path.join(xpdf_path, pdf[:-4], f"page{idx + 1}.png")).convert("RGB")
                    for idx in range(info["page_no"])
                }
                

                # for figure in figures:
                #     page_no = int(figure[:-4][4:])
                #     # page_fig= images[page_no -1]
                #     page_fig = page_pngs[page_no]
                #     rendered_size = page_fig.size

                #     bboxes = figures[figure]
                #     order_no = 0
                #     for bbox in bboxes:
                #         order_no = order_no + 1
                #         png_ratio = float(rendered_size[1])/info['page_height']
                #         print("past",png_ratio)

                #         if len(bbox[1])>0:
                #             data[pdf]['figures'].append({'page': page_no,
                #                           'region_bb': bbox[0],
                #                          'figure_type': 'Figure',
                #                         'page_width': info['page_width'],
                #                         'page_height': info['page_height'],
                #                         'caption_bb': bbox[1][0],
                #                         'caption_text': bbox[1][1]
                #                          })
                #             with open(output_file_path+'/'+str(page_no)+'_'+str(order_no)+'.txt', 'w') as capoutput:
                #                 capoutput.write(str(bbox[1][1]))
                #                 capoutput.close
                #         else:
                #             data[pdf]['figures'].append({'page': page_no,
                #                                      'region_bb': bbox[0],
                #                                      'figure_type': 'Figure',
                #                                      'page_width': info['page_width'],
                #                                      'page_height': info['page_height'],
                #                                      'caption_bb': [],
                #                                      'caption_text': []
                #                                      })
                #         print("past figure bbox", [int(bbox[0][0]*png_ratio), int(bbox[0][1]*png_ratio), 
                #                         int((bbox[0][0]+bbox[0][2])*png_ratio), int((bbox[0][1]+bbox[0][3])*png_ratio)])
                #         fig_extracted = page_fig.crop([int(bbox[0][0]*png_ratio), int(bbox[0][1]*png_ratio), 
                #                         int((bbox[0][0]+bbox[0][2])*png_ratio), int((bbox[0][1]+bbox[0][3])*png_ratio)])
                #         fig_extracted.save(output_file_path+'/'+str(page_no)+'_'+str(order_no)+'.jpg')

                # pprint(data)

                if not flag:
                    continue  # or handle failure
                    # TODO log the error
                    # TODO remove the data dict

                summary = {
                    "filename": pdf,
                    "page_count": info["page_no"],
                    "figure_count_estimate": info.get("fig_no_est", 0),
                    "page_dimensions": {
                        "width": info.get("page_width"),
                        "height": info.get("page_height"),
                    },
                    "figures": [],
                }
                total_index = 0


                for page_name, entries in figures.items():
                    page_no = int(page_name[4:-4])
                    page_fig = page_pngs[page_no]
                    rendered_size = page_fig.size

                    for idx, bbox in enumerate(entries, start=1):
                        total_index += 1
                        png_ratio = float(rendered_size[1])/info['page_height']
                        print("png_ratio",png_ratio)

                        # original code has the below - but we will not be transforming the coordinates to png style
                        # because we want to go back to the pdf and annotate the figure bbox on the pdf page

                        figure_bbox = bbox[0] 

                        # scale_x = rendered_size[0] / info["page_width"]
                        # scale_y = rendered_size[1] / info["page_height"]
                        # pixel_bbox = [
                        #     int((bbox[0][0]) * scale_x),
                        #     int((bbox[0][1]) * scale_y),
                        #     int((bbox[0][0] + bbox[0][2]) * scale_x),
                        #     int((bbox[0][1] + bbox[0][3]) * scale_y),
                        # ]


                        pixel_figure_bbox = [[int(bbox[0][0]*png_ratio), int(bbox[0][1]*png_ratio), 
                                        int((bbox[0][0]+bbox[0][2])*png_ratio), int((bbox[0][1]+bbox[0][3])*png_ratio)]]

                        caption_bbox, caption_text = (bbox[1] if bbox[1] else (None, []))

                        summary["figures"].append({
                            "figure_number": total_index,
                            "page_number": page_no,
                            "page_figure_index": idx,
                            "figure_bbox": figure_bbox,
                            "pixel_figure_bbox": pixel_figure_bbox,
                            "pixel_png_ratio": png_ratio, 
                            "caption_bbox": caption_bbox,
                            "caption_text_lines": caption_text,
                            "page_width": info["page_width"],
                            "page_height": info["page_height"],
                            'region_bb': bbox[0]
                        })

                # json_file = output_file_path+'/'+ pdf[:-4]+'.json'
                # with open(json_file, 'w') as outfile:
                #     json.dump(data, outfile)

                output_dir = os.path.join(output_path, pdf[:-4])
                os.makedirs(output_dir, exist_ok=True)
                with open(output_json, "w") as fh:
                    json.dump(summary, fh, indent=2)
