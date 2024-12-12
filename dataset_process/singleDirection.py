import csv
from collections import defaultdict

def normalize_and_sum_relationships(input_file, output_file):
    # 使用字典存储规范化后的边及其合作次数
    relationship_counts = defaultdict(int)
    
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # 复制表头
        headers = next(reader)
        writer.writerow(headers)
        
        for row in reader:
            start_id, end_id, rel_type, count = row
            count = int(count)
            
            # 将关系方向规范为 start_id < end_id
            if start_id > end_id:
                start_id, end_id = end_id, start_id
            
            # 使用 tuple 作为键，记录合作次数
            relationship_counts[(start_id, end_id, rel_type)] += count

        # 将合并后的关系写回文件
        for (start_id, end_id, rel_type), total_count in relationship_counts.items():
            writer.writerow([start_id, end_id, rel_type, total_count])

# 调用函数对 relationships.csv 进行处理
normalize_and_sum_relationships('relationships.csv', 'relationships_normalized.csv')
