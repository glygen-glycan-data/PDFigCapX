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
import fitz
import shutil


class Figure_Search:

    def figures_info(self, pdf):
        '''accepts a pdf - use Image Manager (if multiple pdf's, folders of pdfs??)'''

        # pdf_full_path = os.path.join(self.input_path, pdf)
        # basepath = os.path.dirname(pdf)
        # basename = os.path.splitext(os.path.basename(pdf))[0]
        basename = os.path.splitext(pdf)[0]
        output_json = basename + '_figures.json'
    
        data = {}

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
                    figures, info = figures_captions_list(pdf)
                    flag = 1

                except Exception as exc:
                    wrong_count = wrong_count +1
                    time.sleep(5)
                    print("Retrying figures_captions_list for {} ({})".format(pdf, exc))
    
            data[pdf]['fig_no'] = info['fig_no_est']

            # output_file_path = os.path.join(self.output_path, pdf[:-4])
            # if not os.path.isdir(output_file_path):
            #     os.mkdir(output_file_path)      

            if not flag:
                # continue  # or handle failure
                # TODO log the error
                # TODO remove the data dict
                pass

            summary = {
                "filename": pdf,
                "total_pages": info["page_no"],
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
                for idx, bbox in enumerate(entries, start=1):
                    total_index += 1
                    x,y,w,h = bbox[0]    # note: x,y,w,h --> in pdf points
                    # page_h = info.get("page_height")
                    # dpi = info.get("dpi", 300) 

                    # x0_pdf = x0
                    # y0_pdf = y0
                    # x1_pdf = x0 + x1
                    # y1_pdf = y0 + y1

                    # figure_bbox = 

                    caption_bbox, caption_text = (bbox[1] if bbox[1] else (None, []))

                    summary["figures"].append({
                        "figure_number": total_index,
                        "page_number": page_no,
                        "page_figure_index": idx,
                        "figure_bbox": [x,y,w,h],
                        "caption_bbox": caption_bbox,
                        "caption_text": caption_text,
                        "page_width": info.get("page_width"),
                        "page_height": info.get("page_height"),
                    })

            # json_file = output_file_path+'/'+ pdf[:-4]+'.json'
            # with open(json_file, 'w') as outfile:
            #     json.dump(data, outfile)

            # output_dir = os.path.join(self.output_path, pdf[:-4])
            # os.makedirs(output_dir, exist_ok=True)

            # with open(output_json, "w") as fh:
            #     json.dump(summary, fh, indent=2)

        # delete the folder which contains extra data (folder with all flattened pages and intermediate json file)
        # note that athejson file with the figures data will still continue to exist and will be named as: <pdf_name>_figures.json
        pages_dir = pdf.rsplit('.')[0]
        shutil.rmtree(pages_dir)

        return summary

    def draw_annotations(self, pdf_path, json_file):

        #     basename = os.path.splitext(os.path.basename(pdf_path))[0]
        # doc = fitz.open(pdf_path)
        basename = os.path.splitext(pdf_path)[0]

        doc = fitz.open(pdf_path)

        with open(json_file) as f:
            data = json.load(f)

        for result in data.get("figures", []):
            page = doc[result['page_number']-1]

            x,y,w,h = result['figure_bbox']

            try:
                rect = fitz.Rect(x, y, x + w, y + h) 
                annot = page.add_rect_annot(rect)

                # set fig id
                annot.set_info(content=f"fig:{result['figure_number']}")
                annot.update()
            except Exception as e:
                print(f"\nException occured {e}")

        doc.save(basename + ".annotated.pdf")
        print("NOTE: please incorporate other information like captions etc as well in results.json")



if __name__ == '__main__':


    fs = Figure_Search()
    pdf_path = 'path.pdf'
    fig_json_path = fs.figures_info(pdf_path)
