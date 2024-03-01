def deduplicate_job_titles(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 去重处理
    unique_job_titles = list(set(lines))

    with open(output_file, 'w', encoding='utf-8') as file:
        for title in unique_job_titles:
            file.write(title)


# 示例用法
input_file = 'title.txt'
output_file = 'unique_title.txt'
deduplicate_job_titles(input_file, output_file)
