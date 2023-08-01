from flask import Flask, request, jsonify, send_file
from barcode import Code128
from barcode.writer import ImageWriter
from pathlib import Path
import os
from PIL import Image
import io
import base64
import xhtml2pdf.pisa as pisa

app = Flask(__name__)

@app.route('/gerar-boleto', methods=['POST'])
def gerar_boleto():
    dados = request.get_json()

    campos_obrigatorios = ['codigo_dv_banco', 'linha_digitavel', 'local_pagamento', 'data_vencimento', 'cedente', 'agencia_conta_cedente', 'data_documento', 'numero_documento', 'especie_documento', 'aceite', 'data_processamento', 'nosso_numero_format', 'carteira', 'especie', 'quantidade', 'valor', 'valor_documento', 'instrucoes', 'pagador_nome', 'CPF_CNPJ', 'codbanco', 'instrucoes']
    campos_vazios = [campo for campo in campos_obrigatorios if campo not in dados or not dados[campo]]

    if campos_vazios:
        campos_vazios_str = ', '.join(campos_vazios)
        return jsonify({'error': f'Campos obrigatórios vazios: {campos_vazios_str}'}), 400

    # Gerar o código de barras
    caminho_codigo_barras = gerar_codigo_barras(dados)

    # Carregar o modelo HTML
    with open('modelo.html', 'r') as file:
        template = file.read()

    # Substituir as variáveis do modelo pelos dados do boleto
    html = template.replace('${codigo_dv_banco}', dados['codigo_dv_banco']) \
                   .replace('${linha_digitavel}', dados['linha_digitavel']) \
                   .replace('${local_pagamento}', dados['local_pagamento']) \
                   .replace('${data_vencimento}', dados['data_vencimento']) \
                   .replace('${cedente}', dados['cedente']) \
                   .replace('${agencia_conta_cedente}', dados['agencia_conta_cedente']) \
                   .replace('${data_documento}', dados['data_documento']) \
                   .replace('${numero_documento}', dados['numero_documento']) \
                   .replace('${especie_documento}', dados['especie_documento']) \
                   .replace('${aceite}', dados['aceite']) \
                   .replace('${data_processamento}', dados['data_processamento']) \
                   .replace('${nosso_numero_format}', dados['nosso_numero_format']) \
                   .replace('${carteira}', dados['carteira']) \
                   .replace('${especie}', dados['especie']) \
                   .replace('${quantidade}', dados['quantidade']) \
                   .replace('${valor}', dados['valor']) \
                   .replace('${valor_documento}', dados['valor_documento']) \
                   .replace('${instrucoes}', dados['instrucoes']) \
                   .replace('${pagador}', dados['pagador_nome']) \
                   .replace('${CPF_CNPJ}', dados['CPF_CNPJ']) \
                   .replace('${instrucoes}', dados['instrucoes']) \
                   .replace('${codbanco}', dados['codbanco']) \
                   .replace('${codigo_barras}', get_base64_image(caminho_codigo_barras))  # Substituir pela imagem em base64

    # Converter HTML para PDF
    output_path = 'boleto.pdf'
    with open(output_path, 'wb') as file:
        pisa.CreatePDF(html, dest=file)

    # Retornar o link de download do PDF
    download_url = request.host_url + 'download/' + output_path  # URL completa incluindo o nome do arquivo
    return jsonify({'link_pdf': download_url})

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    allowed_files = ['boleto.pdf', 'outro_arquivo.pdf', 'arquivo_qualquer.txt']

    if filename not in allowed_files:
        client_ip = request.remote_addr
        error_message = f"Arquivo não encontrado. IP: {client_ip}"
        return jsonify({'error': error_message}), 404

    # Verificar se o arquivo é permitido para download
    if filename in ['boleto.py', 'modelo.html']:
        return jsonify({'error': 'Acesso negado.'}), 403

    path = os.path.join(app.root_path, filename)
    if os.path.isfile(path):
        return send_file(path, as_attachment=True)
    else:
        client_ip = request.remote_addr
        error_message = f"Arquivo não encontrado. IP: {client_ip}"
        return jsonify({'error': error_message}), 404

def gerar_codigo_barras(dados):
    barcode_value = dados['barcode']
    barcode_path = f'barcode.png'

    # Gerar o código de barras Code 128
    code = Code128(barcode_value, writer=ImageWriter())
    code.write(barcode_path, options={'module_width': 0.5, 'module_height': 15})  # Ajuste os parâmetros de tamanho conforme necessário

    return barcode_path

def get_base64_image(image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()

    base64_image = base64.b64encode(image_data).decode('utf-8')
    return 'data:image/png;base64,' + base64_image

if __name__ == '__main__':
    app.run()
