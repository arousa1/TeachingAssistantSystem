"""
LLM 提示模板集中管理
后续想改分类规则、加语言、调置信度，只改这里。
"""
CLASSIFY_PROMPT = """
You are a file-type expert.  
Given the file name and optional header bytes, output **only** a JSON object:
{
  "type": "code/doc/other",
  "language": "py/js/ts/c/cpp/pdf/md/doc/docx/..",   // if code or doc
  "confidence": 0.95
}
Rules:
- type=code  : source code / script / executable
- type=doc   : pdf, word, ppt, markdown, txt, csv
- type=image : png/jpg/svg/bmp
- type=archive: zip/7z/tar/gz/rar
- type=other : not above
"""