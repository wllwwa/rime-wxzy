# 万象用户词库修改工具

# ==================== 用户配置区域（请根据实际情况修改） ====================
# 文件路径配置
MODS_FILE = 'D:/Rime/config/cn_dicts_user/modifications.txt'  # 修改规则文件：刷辅助码(重点)、修改词条
ADDS_FILE = 'D:/Rime/config/cn_dicts_user/additions.txt'      # 新增词条文件：定义需要添加的新词条
DELETIONS_FILE = 'D:/Rime/config/cn_dicts_user/deletions.txt'  # 删除词条文件：定义需要删除的词条
NEUTRAL_TONE_FILE = 'D:/Rime/config/cn_dicts_user/neutral_tone.txt'  # 轻声对应表：定义轻声与有声调的拼音对应关系
# 词库目录配置
DICTS_FOLDER = 'D:/Rime/config/dicts/'  # Rime词库文件所在目录
USER_EXTEND_FILE = 'chars.pro.dict.yaml'  # 用户扩展文件：所有新增词条将统一存储在此文件中,默认'chars.pro.dict.yaml',也可用packs拓展词库，请根据实际情况修改
EXCLUDE_FILES = [  # 排除文件列表：这些文件不会被处理
    'fuhao.pro.dict.yaml',     # 符号词库
    'en.dict.yaml',            # 英文词库
    'corrections.pro.dict.yaml', # 纠错词库
    'cn&en.dict.yaml'          # 中英混合词库
]
# 性能配置
USE_PARALLEL = True  # 是否启用并行处理：True=启用（推荐），False=禁用
MAX_WORKERS = None   # 最大工作进程数：None=自动检测CPU核心数，可设置为具体数字（如4）
# ===========================================================================

import os
import glob
import sys

# 禁用字节码生成，减少磁盘I/O
sys.dont_write_bytecode = True

# 配置缓存
_config_cache = {}

def load_neutral_tone_map():
    """加载轻声对应表"""
    neutral_tone_map = {}  # {(汉字, 轻声拼音): 有声调拼音}
    
    if not os.path.exists(NEUTRAL_TONE_FILE):
        print(f"注意：未找到轻声对应表文件 {NEUTRAL_TONE_FILE}（跳过轻声处理）")
        return neutral_tone_map
        
    try:
        with open(NEUTRAL_TONE_FILE, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                
                if len(parts) >= 3:
                    hanzi = parts[0]
                    neutral_pinyin = parts[1]  # 轻声拼音（无声调）
                    tonal_pinyin = parts[2]    # 有声调拼音
                    
                    neutral_tone_map[(hanzi, neutral_pinyin)] = tonal_pinyin
                    
        print(f"加载轻声对应表: 共 {len(neutral_tone_map)} 条规则")
    except Exception as e:
        print(f"读取轻声对应表文件出错: {e}")
    
    return neutral_tone_map
def expand_modifications_with_neutral_tone(mods, multi_mods, neutral_tone_map):
    """使用轻声对应表扩展修改规则"""
    expanded_mods = mods.copy()       # 扩展后的单字修改规则
    expanded_multi_mods = multi_mods.copy()  # 扩展后的多字词修改规则
    
    # 处理单字修改规则
    neutral_added_count = 0
    for (hanzi, pinyin), (code, freq) in mods.items():
        # 检查这个拼音是否有对应的轻声版本
        for (neutral_hanzi, neutral_pinyin), tonal_pinyin in neutral_tone_map.items():
            if neutral_hanzi == hanzi and tonal_pinyin == pinyin:
                # 添加轻声拼音的修改规则
                expanded_mods[(hanzi, neutral_pinyin)] = (code, freq)
                neutral_added_count += 1
                # print(f"添加轻声规则: {hanzi} {neutral_pinyin} -> {code}")
    
    # 处理多字词修改规则（如果需要的话）
    # 这里可以根据需要添加多字词的轻声处理逻辑
    
    # print(f"轻声规则扩展完成: 新增 {neutral_added_count} 条轻声修改规则")
    return expanded_mods, expanded_multi_mods


def load_modifications():
    """加载修改规则（支持单字和多字词）- 带缓存"""
    cache_key = 'modifications'
    if cache_key in _config_cache:
        return _config_cache[cache_key]
        
    mods = {}       # 单字修改规则: {(汉字, 拼音): (新形码, 新词频)}
    multi_mods = {} # 多字词修改规则: {词条: (新编码, 新词频)}
    
    if not os.path.exists(MODS_FILE):
        print(f"错误：找不到修改规则文件 {MODS_FILE}")
        _config_cache[cache_key] = (mods, multi_mods)
        return mods, multi_mods
        
    try:
        with open(MODS_FILE, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                
                if len(parts) >= 2:  # 至少需要汉字和编码部分
                    hanzi = parts[0]
                    encoding = parts[1]
                    freq = parts[2] if len(parts) >= 3 else ""
                    
                    # 处理单字规则
                    if len(hanzi) == 1:
                        if ';' in encoding:
                            pinyin, code = encoding.split(';', 1)
                            mods[(hanzi, pinyin)] = (code, freq)
                    
                    # 处理多字词规则
                    elif len(hanzi) > 1:
                        multi_mods[hanzi] = (encoding, freq)
                        
    except Exception as e:
        print(f"读取修改规则文件出错: {e}")
    
    _config_cache[cache_key] = (mods, multi_mods)
    return mods, multi_mods

def load_additions():
    """加载新增词条 - 带缓存"""
    cache_key = 'additions'
    if cache_key in _config_cache:
        return _config_cache[cache_key]
        
    adds = []
    if not os.path.exists(ADDS_FILE):
        print(f"注意：未找到新增词条文件 {ADDS_FILE}（跳过新增操作）")
        _config_cache[cache_key] = adds
        return adds
        
    try:
        with open(ADDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:  # 至少需要汉字和编码
                    hanzi = parts[0]
                    encoding = parts[1]
                    freq = parts[2] if len(parts) >= 3 else "1"
                    adds.append((hanzi, encoding, freq))
    except Exception as e:
        print(f"读取新增词条文件出错: {e}")
    
    _config_cache[cache_key] = adds
    return adds

def load_deletions():
    """加载要删除的词条列表 - 带缓存"""
    cache_key = 'deletions'
    if cache_key in _config_cache:
        return _config_cache[cache_key]
        
    deletions = set()
    if not os.path.exists(DELETIONS_FILE):
        print(f"注意：未找到删除文件 {DELETIONS_FILE}（跳过删除操作）")
        _config_cache[cache_key] = deletions
        return deletions
        
    try:
        with open(DELETIONS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    hanzi = parts[0]
                    encoding = parts[1]
                    
                    # 提取拼音部分
                    pinyin_part = extract_pinyin_part(encoding)
                    if pinyin_part:
                        deletions.add((hanzi, pinyin_part))
    except Exception as e:
        print(f"读取删除文件出错: {e}")
    
    _config_cache[cache_key] = deletions
    return deletions

def extract_pinyin_part(encoding):
    """从编码中提取拼音部分"""
    if ';' in encoding:
        if ' ' in encoding:
            # 多字词：提取每个音节的拼音部分
            pinyin_parts = []
            for enc_part in encoding.split():
                if ';' in enc_part:
                    pinyin_parts.append(enc_part.split(';', 1)[0])
                else:
                    pinyin_parts.append(enc_part)
            return ' '.join(pinyin_parts)
        else:
            # 单字：直接提取拼音
            return encoding.split(';', 1)[0]
    else:
        return encoding

def is_chars_dict(filename):
    """简单判断是否为单字词库文件（文件名包含"char"）"""
    filename_lower = filename.lower()
    return 'char' in filename_lower

def should_process_entry(hanzi, encoding, deletions):
    """检查词条是否需要处理（是否在删除列表中）"""
    pinyin_part = extract_pinyin_part(encoding)
    return (hanzi, pinyin_part) not in deletions

def process_single_line(line, mods, multi_mods, deletions):
    """处理单行词条"""
    line = line.rstrip('\n')
    
    # 保留元数据行
    if line.startswith('#') or line in ('---', '...'):
        return line
    
    # 处理有效词条
    parts = line.split('\t')
    if len(parts) == 3:
        hanzi, encoding, freq = parts
        
        # 检查是否需要删除
        if not should_process_entry(hanzi, encoding, deletions):
            return None  # 标记为删除
        
        # 处理多字词修改规则
        if len(hanzi) > 1 and hanzi in multi_mods:
            new_encoding, new_freq = multi_mods[hanzi]
            if not new_freq.strip():
                new_freq = freq
            return f"{hanzi}\t{new_encoding}\t{new_freq}"
        
        # 处理单字修改规则
        if len(hanzi) == 1:
            if ';' in encoding:
                p, c = encoding.split(';', 1)
                mod_key = (hanzi, p)
                if mod_key in mods:
                    new_code, new_freq = mods[mod_key]
                    if not new_freq.strip():
                        new_freq = freq
                    return f"{hanzi}\t{p};{new_code}\t{new_freq}"
            else:
                # 处理没有形码的单字条目
                p = encoding
                mod_key = (hanzi, p)
                if mod_key in mods:
                    new_code, new_freq = mods[mod_key]
                    if not new_freq.strip():
                        new_freq = freq
                    return f"{hanzi}\t{p};{new_code}\t{new_freq}"
        
        # 处理多字词中的单字修改（逐字检查）
        elif len(hanzi) > 1:
            return process_multi_char_line(hanzi, encoding, freq, mods)
    
    return line

def process_multi_char_line(hanzi, encoding, freq, mods):
    """处理多字词中的单字修改"""
    enc_parts = []
    modified = False
    
    # 拆分现有编码
    for enc in encoding.split():
        if ';' in enc:
            p, c = enc.split(';', 1)
            enc_parts.append((p, c))
        else:
            enc_parts.append((enc, ''))
    
    # 检查每个字是否需要修改
    new_enc_parts = []
    for char, (p, c) in zip(hanzi, enc_parts):
        mod_key = (char, p)
        if mod_key in mods:
            new_code, _ = mods[mod_key]  # 多字词中的单字修改只改形码，不改词频
            new_enc_parts.append(f"{p};{new_code}")
            modified = True
        else:
            new_enc_parts.append(f"{p};{c}" if c else p)
    
    if modified:
        new_encoding = ' '.join(new_enc_parts)
        return f"{hanzi}\t{new_encoding}\t{freq}"
    
    return f"{hanzi}\t{encoding}\t{freq}"

def sort_entries(entries):
    """对词条进行排序：先按词条长度（字数），再按词条内容"""
    return sorted(entries, key=lambda x: (len(x[0]), x[0]))

def get_dict_files():
    """获取目录下所有的词库文件（排除指定文件）"""
    pattern = os.path.join(DICTS_FOLDER, '*.yaml')
    
    # 确保USER_EXTEND_FILE存在
    user_extend_path = os.path.join(DICTS_FOLDER, USER_EXTEND_FILE)
    if not os.path.exists(user_extend_path):
        print(f"注意：{USER_EXTEND_FILE} 不存在，将创建新文件")
        # 从文件名中提取name（去掉.dict.yaml后缀）
        dict_name = USER_EXTEND_FILE.replace('.dict.yaml', '')
        # 创建基础的用户扩展文件
        with open(user_extend_path, 'w', encoding='utf-8') as f:
            f.write(f"""# Rime user dictionary
# 用户自定义词库
---
name: {dict_name}
version: "LTS"
sort: by_weight
...
""")
    
    # 获取所有yaml文件（包括新创建的user_extend.dict.yaml）
    dict_files = glob.glob(pattern)
    
    # 过滤掉排除的文件
    filtered_files = []
    for file_path in dict_files:
        filename = os.path.basename(file_path)
        if filename not in EXCLUDE_FILES:
            filtered_files.append(file_path)
        else:
            print(f"跳过排除文件: {filename}")
    
    return filtered_files

def process_single_dict_file(args):
    """处理单个词库文件 - 用于并行处理"""
    file_path, mods, multi_mods, adds, deletions = args
    filename = os.path.basename(file_path)
    
    temp_file = file_path + '.tmp'
    is_user_extend_file = (filename == USER_EXTEND_FILE)
    
    modified_count = 0
    multi_modified_count = 0
    deleted_count = 0
    
    try:
        # 第一遍：收集已存在的词条（只记录汉字和编码）
        existing_entries = set()
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or line in ('---', '...'):
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        hanzi = parts[0]
                        encoding = parts[1]
                        existing_entries.add((hanzi, encoding))
        
        # 第二遍：处理文件
        with open(file_path, 'r', encoding='utf-8') as fin, \
             open(temp_file, 'w', encoding='utf-8') as fout:
            
            # 处理现有内容
            entries_to_sort = []  # 用于收集需要排序的词条（仅USER_EXTEND_FILE使用）
            in_metadata = True   # 标记是否在元数据部分
            
            for line in fin:
                processed_line = line.rstrip('\n')
                
                # 检查是否结束元数据部分
                if in_metadata and processed_line == '...':
                    in_metadata = False
                    fout.write(processed_line + '\n')
                    continue
                
                # 元数据行直接写入
                if in_metadata:
                    fout.write(processed_line + '\n')
                    continue
                
                # 处理词条行
                processed_line = process_single_line(processed_line, mods, multi_mods, deletions)
                
                if processed_line is None:
                    deleted_count += 1
                    continue
                
                # 统计修改数量
                original_line = line.rstrip('\n')
                if processed_line != original_line and not processed_line.startswith('#'):
                    if len(processed_line.split('\t')[0]) > 1:
                        multi_modified_count += 1
                    else:
                        modified_count += 1
                
                # 如果是USER_EXTEND_FILE且是词条行，收集起来用于排序
                if is_user_extend_file:
                    parts = processed_line.split('\t')
                    if len(parts) >= 2:
                        entries_to_sort.append(parts)
                else:
                    fout.write(processed_line + '\n')
            
            # 对于USER_EXTEND_FILE，添加新词条并排序
            if is_user_extend_file:
                added_count = 0
                new_entries = []
                
                # 收集新增词条（去重检查）
                for entry in adds:
                    hanzi, encoding, freq = entry
                    
                    if not should_process_entry(hanzi, encoding, deletions):
                        continue
                    
                    # 检查是否已存在（去重）
                    if (hanzi, encoding) in existing_entries:
                        continue
                    
                    # 对新增词条应用修改规则
                    processed_entry = process_single_line(f"{hanzi}\t{encoding}\t{freq}", mods, multi_mods, deletions)
                    
                    # 如果词条被删除，跳过
                    if processed_entry is None:
                        continue
                    
                    # 解析处理后的词条
                    parts = processed_entry.split('\t')
                    if len(parts) >= 2:
                        processed_hanzi = parts[0]
                        processed_encoding = parts[1]
                        processed_freq = parts[2] if len(parts) >= 3 else freq
                        
                        # 再次检查去重（处理后的词条可能已存在）
                        if (processed_hanzi, processed_encoding) not in existing_entries:
                            new_entries.append([processed_hanzi, processed_encoding, processed_freq])
                            added_count += 1
                
                # 合并现有词条和新增词条
                all_entries = entries_to_sort + new_entries
                
                # 按词条长度和内容排序
                sorted_entries = sort_entries(all_entries)
                
                # 写入排序后的词条
                for hanzi, encoding, freq in sorted_entries:
                    fout.write(f"{hanzi}\t{encoding}\t{freq}\n")
            else:
                # 其他文件只处理修改和删除，不添加新词条
                added_count = 0
        
        # 原子替换文件
        os.replace(temp_file, file_path)
        return {
            'filename': filename,
            'modified': modified_count,
            'multi_modified': multi_modified_count,
            'added': added_count,
            'deleted': deleted_count,
            'success': True
        }
        
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return {
            'filename': filename,
            'modified': 0,
            'multi_modified': 0,
            'added': 0,
            'deleted': 0,
            'success': False,
            'error': str(e)
        }



def process_dict_files_parallel(dict_files, mods, multi_mods, adds, deletions):
    """并行处理多个词库文件"""
    try:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        import multiprocessing
        
        # 自动检测CPU核心数
        if MAX_WORKERS is None:
            max_workers = min(multiprocessing.cpu_count(), len(dict_files))
        else:
            max_workers = min(MAX_WORKERS, len(dict_files))
        
        print(f"使用 {max_workers} 个进程并行处理 {len(dict_files)} 个文件...")
        
        # 准备参数
        tasks = [(file_path, mods, multi_mods, adds, deletions) for file_path in dict_files]
        
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(process_single_dict_file, task): task[0] 
                for task in tasks
            }
            
            # 收集结果
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    filename = os.path.basename(file_path)
                    if result['success']:
                        print(f"✓ {filename} - 完成 (修改:{result['modified']}, 多字:{result['multi_modified']}, 新增:{result['added']}, 删除:{result['deleted']})")
                    else:
                        print(f"✗ {filename} - 失败: {result.get('error', '未知错误')}")
                except Exception as e:
                    print(f"✗ {os.path.basename(file_path)} - 处理异常: {e}")
                    results.append({
                        'filename': os.path.basename(file_path),
                        'success': False,
                        'error': str(e)
                    })
        
        return results
        
    except ImportError:
        print("警告：无法导入concurrent.futures，回退到串行处理")
        return process_dict_files_sequential(dict_files, mods, multi_mods, adds, deletions)

def process_dict_files_sequential(dict_files, mods, multi_mods, adds, deletions):
    """串行处理多个词库文件"""
    results = []
    for file_path in dict_files:
        filename = os.path.basename(file_path)
        print(f"处理: {filename}", end="", flush=True)
        
        # 复用并行处理函数
        result = process_single_dict_file((file_path, mods, multi_mods, adds, deletions))
        results.append(result)
        
        if result['success']:
            print(f" - 完成 (修改:{result['modified']}, 多字:{result['multi_modified']}, 新增:{result['added']}, 删除:{result['deleted']})")
        else:
            print(f" - 失败: {result.get('error', '未知错误')}")
    
    return results

def clear_cache():
    """清空配置缓存"""
    _config_cache.clear()

def main_optimized():
    """主函数"""
    # 预加载所有配置
    print("加载配置文件中...")
    
    # 加载轻声对应表
    neutral_tone_map = load_neutral_tone_map()
    
    # 加载原始修改规则
    mods, multi_mods = load_modifications()
    
    # 使用轻声对应表扩展修改规则
    if neutral_tone_map:
        mods, multi_mods = expand_modifications_with_neutral_tone(mods, multi_mods, neutral_tone_map)
    
    adds = load_additions()
    deletions = load_deletions()
    
    # 获取所有词库文件
    dict_files = get_dict_files()
    
    if not dict_files:
        print(f"错误：在目录 {DICTS_FOLDER} 中未找到任何词库文件")
        return False
    
    print(f"找到 {len(dict_files)} 个词库文件，开始处理...")
    
    # 根据配置选择处理方式
    if USE_PARALLEL and len(dict_files) > 1:
        results = process_dict_files_parallel(dict_files, mods, multi_mods, adds, deletions)
    else:
        results = process_dict_files_sequential(dict_files, mods, multi_mods, adds, deletions)
    
    # 统计总结果
    total_results = {
        'modified': 0,
        'multi_modified': 0, 
        'added': 0,
        'deleted': 0,
        'success_count': 0,
        'fail_count': 0
    }
    
    for result in results:
        if result['success']:
            total_results['modified'] += result['modified']
            total_results['multi_modified'] += result['multi_modified']
            total_results['added'] += result['added']
            total_results['deleted'] += result['deleted']
            total_results['success_count'] += 1
        else:
            total_results['fail_count'] += 1
    
    # 输出统计信息
    print("\n" + "="*50)
    print("操作完成！统计信息:")
    print("="*50)
    print(f"总计:")
    print(f"  • 修改词条: {total_results['modified']} 条")
    print(f"  • 多字词修改: {total_results['multi_modified']} 条") 
    print(f"  • 新增词条: {total_results['added']} 条")
    print(f"  • 删除词条: {total_results['deleted']} 条")
    
    # 清空缓存
    clear_cache()
    return True

# ========================================================

def benchmark():
    """性能测试函数"""
    import time
    start_time = time.time()
    
    print("=" * 60)
    print("开始性能测试...")
    print("=" * 60)
    
    try:
        # 运行主函数
        success = main_optimized()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("性能测试结果:")
        print("=" * 60)
        print(f"总执行时间: {execution_time:.2f} 秒")
        print(f"状态: {'成功' if success else '失败'}")
        
        return execution_time
        
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"\n错误: {e}")
        print(f"执行时间: {execution_time:.2f} 秒")
        return execution_time

# 替换原来的主程序入口
if __name__ == "__main__":
    # 可以选择直接运行性能测试
    if len(sys.argv) > 1 and sys.argv[1] == 'benchmark':
        benchmark()
    else:
        # 或者正常运行
        main_optimized()
