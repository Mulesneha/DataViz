from flask import Flask, render_template, request, jsonify
import csv
import io
import json
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not (file.filename.endswith('.csv') or file.filename.endswith('.tsv')):
        return jsonify({'error': 'Only CSV/TSV files are supported'}), 400
    
    try:
        content = file.read().decode('utf-8-sig')
        delimiter = '\t' if file.filename.endswith('.tsv') else ','
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        rows = list(reader)
        
        if not rows:
            return jsonify({'error': 'CSV file is empty'}), 400
        
        headers = list(rows[0].keys())
        
        # Try to infer numeric columns
        numeric_cols = []
        string_cols = []
        for col in headers:
            try:
                float(rows[0][col].replace(',', ''))
                numeric_cols.append(col)
            except (ValueError, AttributeError):
                string_cols.append(col)
        
        # Convert data
        data = []
        for row in rows:
            record = {}
            for col in headers:
                val = row[col]
                if col in numeric_cols:
                    try:
                        record[col] = float(val.replace(',', ''))
                    except:
                        record[col] = 0
                else:
                    record[col] = val
            data.append(record)
        
        return jsonify({
            'headers': headers,
            'numeric_cols': numeric_cols,
            'string_cols': string_cols,
            'data': data,
            'row_count': len(data)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to parse file: {str(e)}'}), 400

@app.route('/api/manual', methods=['POST'])
def manual_data():
    body = request.get_json()
    if not body:
        return jsonify({'error': 'No data provided'}), 400
    
    raw = body.get('data', '')
    chart_type = body.get('chart_type', 'bar')
    
    try:
        lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
        data = []
        for line in lines:
            parts = [p.strip() for p in line.replace('\t', ',').split(',')]
            if len(parts) >= 2:
                label = parts[0]
                try:
                    values = [float(p) for p in parts[1:]]
                    data.append({'label': label, 'values': values})
                except ValueError:
                    pass
        
        if not data:
            return jsonify({'error': 'Could not parse data. Format: Label, Value1, Value2...'}), 400
        
        return jsonify({'data': data, 'row_count': len(data)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/sample/<dataset>')
def sample_data(dataset):
    samples = {
        'sales': {
            'headers': ['Month', 'Revenue', 'Expenses', 'Profit'],
            'numeric_cols': ['Revenue', 'Expenses', 'Profit'],
            'string_cols': ['Month'],
            'data': [
                {'Month': 'Jan', 'Revenue': 42000, 'Expenses': 28000, 'Profit': 14000},
                {'Month': 'Feb', 'Revenue': 38500, 'Expenses': 25000, 'Profit': 13500},
                {'Month': 'Mar', 'Revenue': 51000, 'Expenses': 31000, 'Profit': 20000},
                {'Month': 'Apr', 'Revenue': 47200, 'Expenses': 29500, 'Profit': 17700},
                {'Month': 'May', 'Revenue': 63000, 'Expenses': 38000, 'Profit': 25000},
                {'Month': 'Jun', 'Revenue': 58800, 'Expenses': 35200, 'Profit': 23600},
                {'Month': 'Jul', 'Revenue': 72000, 'Expenses': 42000, 'Profit': 30000},
                {'Month': 'Aug', 'Revenue': 68500, 'Expenses': 40000, 'Profit': 28500},
                {'Month': 'Sep', 'Revenue': 55000, 'Expenses': 33000, 'Profit': 22000},
                {'Month': 'Oct', 'Revenue': 61000, 'Expenses': 36000, 'Profit': 25000},
                {'Month': 'Nov', 'Revenue': 79000, 'Expenses': 45000, 'Profit': 34000},
                {'Month': 'Dec', 'Revenue': 91000, 'Expenses': 52000, 'Profit': 39000},
            ]
        },
        'market': {
            'headers': ['Category', 'Share'],
            'numeric_cols': ['Share'],
            'string_cols': ['Category'],
            'data': [
                {'Category': 'Electronics', 'Share': 34.2},
                {'Category': 'Clothing', 'Share': 22.8},
                {'Category': 'Food & Bev', 'Share': 18.5},
                {'Category': 'Home Goods', 'Share': 12.1},
                {'Category': 'Sports', 'Share': 7.4},
                {'Category': 'Other', 'Share': 5.0},
            ]
        },
        'scatter': {
            'headers': ['Name', 'Age', 'Income', 'Score'],
            'numeric_cols': ['Age', 'Income', 'Score'],
            'string_cols': ['Name'],
            'data': [
                {'Name': 'Sneha', 'Age': 28, 'Income': 65000, 'Score': 82},
                {'Name': 'Bob', 'Age': 35, 'Income': 92000, 'Score': 76},
                {'Name': 'Carol', 'Age': 42, 'Income': 118000, 'Score': 88},
                {'Name': 'Dave', 'Age': 24, 'Income': 48000, 'Score': 70},
                {'Name': 'Eve', 'Age': 31, 'Income': 78000, 'Score': 85},
                {'Name': 'Frank', 'Age': 55, 'Income': 145000, 'Score': 91},
                {'Name': 'Grace', 'Age': 29, 'Income': 61000, 'Score': 79},
                {'Name': 'Hank', 'Age': 47, 'Income': 132000, 'Score': 87},
                {'Name': 'Iris', 'Age': 38, 'Income': 99000, 'Score': 83},
                {'Name': 'Jake', 'Age': 26, 'Income': 54000, 'Score': 72},
                {'Name': 'Kate', 'Age': 33, 'Income': 84000, 'Score': 86},
                {'Name': 'Leo', 'Age': 61, 'Income': 158000, 'Score': 93},
            ]
        }
    }
    
    if dataset not in samples:
        return jsonify({'error': 'Unknown sample dataset'}), 404
    
    d = samples[dataset]
    d['row_count'] = len(d['data'])
    return jsonify(d)

if __name__ == '__main__':
    app.run(debug=True, port=5000)