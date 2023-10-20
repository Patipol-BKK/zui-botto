import re
import discord_markdown_ast_parser

def parse_text_segment(text_segment):
    node_type = 'TEXT'
    code_lang = ''
    parsed_text = ''
    # Markdown stylings
    if text_segment['node_type'] == 'TEXT':
        parsed_text = text_segment['text_content']
    elif text_segment['node_type'] == 'ITALIC':
        parsed_text = '_'
        for child in text_segment['children']:
            parsed_text += parse_text_segment(child)['text_content']
        parsed_text += '_'
    elif text_segment['node_type'] == 'BOLD':
        parsed_text = '**'
        for child in text_segment['children']:
            parsed_text += parse_text_segment(child)['text_content']
        parsed_text += '**'
    elif text_segment['node_type'] == 'UNDERLINE':
        parsed_text = '__'
        for child in text_segment['children']:
            parsed_text += parse_text_segment(child)['text_content']
        parsed_text += '__'
    elif text_segment['node_type'] == 'STRIKETHROUGH':
        parsed_text = '~~'
        for child in text_segment['children']:
            parsed_text += parse_text_segment(child)['text_content']
        parsed_text += '~~'
    elif text_segment['node_type'] == 'SPOILER':
        parsed_text = '||'
        for child in text_segment['children']:
            parsed_text += parse_text_segment(child)['text_content']
        parsed_text += '||'
    elif text_segment['node_type'] == 'CODE_INLINE':
        parsed_text = '`'
        for child in text_segment['children']:
            parsed_text += parse_text_segment(child)['text_content']
        parsed_text += '`'
        
    # Blocks
    elif text_segment['node_type'] == 'QUOTE_BLOCK':
        node_type = 'QUOTE_BLOCK'
        for child in text_segment['children']:
            parsed_text += parse_text_segment(child)['text_content']
    elif text_segment['node_type'] == 'CODE_BLOCK':
        node_type = 'CODE_BLOCK'
        try:
            code_lang = text_segment['code_lang']
        except:
            pass

        for child in text_segment['children']:
            parsed_text += parse_text_segment(child)['text_content']
            
    return {
        'node_type': node_type,
        'code_lang': code_lang,
        'text_content': parsed_text
    }

def segment_block(segment, pattern):
    split_segments = []
    double_split_indices = [0]
    
    text = segment['text_content']
    
    for m in re.finditer(pattern, text):
        double_split_indices.append(m.start())
    double_split_indices.append(len(text))
    for idx, split_idx in enumerate(double_split_indices):
        if idx < len(double_split_indices) - 1:
            split_segments.append({
                'node_type': segment['node_type'],
                'code_lang': segment['code_lang'],
                'text_content': text[double_split_indices[idx]: double_split_indices[idx + 1]]
                
            })

    return split_segments

def segment_block_by_length(segment, max_length):
    split_segments = []
    idx = 0
    text = segment['text_content']
    
    markdown_length = 0
    if segment['node_type'] == 'QUOTE_BLOCK':
        markdown_length += len('> ')
    elif segment['node_type'] == 'CODE_BLOCK':
        markdown_length += len('```')*2 + len(segment['code_lang']) + len('\n')
    
    while True:
#         print(idx)
        if idx >= len(text):
            break
        else:
            split_segments.append({
                'node_type': segment['node_type'],
                'code_lang': segment['code_lang'],
                'text_content': text[idx:min(idx + max_length - markdown_length, len(text))]
            })
        idx += max_length - markdown_length
        
#     print(split_segments)
    return split_segments

def merge_block(segment1, segment2):
    return {
        'node_type': segment1['node_type'],
        'code_lang': segment1['code_lang'],
        'text_content': segment1['text_content'] + segment2['text_content']
    }

def get_block_length(segment):
    length = len(segment['text_content'])
    if segment['node_type'] == 'QUOTE_BLOCK':
        length += len('> ')
    elif segment['node_type'] == 'CODE_BLOCK':
        length += len('```')*2 + len(segment['code_lang']) + len('\n')
        
    return length
        
def get_merged_block_length(segment1, segment2):
    length = len(segment1['text_content']) + len(segment2['text_content'])
    if segment1['node_type'] == 'QUOTE_BLOCK':
        length += len('> ')
    elif segment1['node_type'] == 'CODE_BLOCK':
        length += len('```')*2 + len(segment1['code_lang']) + len('\n')
        
    return length
    
def segment_markdown(text, max_length):
    # Segment text to blocks according to text or code/quote blocks
    text_segments = []
    try:
        markdown_segments = discord_markdown_ast_parser.parse_to_dict(text)
        add_newline = True
        for segment in markdown_segments:
            if segment['node_type'] == 'QUOTE_BLOCK' or segment['node_type'] == 'CODE_BLOCK':
                text_segments.append(parse_text_segment(segment))
                add_newline = True
            else: 
                if add_newline:
                    text_segments.append(parse_text_segment(segment))
                    add_newline = False
                else:
                    text_segments[-1]['text_content'] += parse_text_segment(segment)['text_content']
    except Exception as e:
        # If segmentation unsuccessful, fall back to treating text as a single normal text block
        print(e)
        text_segments.append({
            'node_type': 'TEXT',
            'code_lang': '',
            'text_content': text
        })
        
    # Segment text to smallest possible blocks
    trimmed_segments = []
    for segment in text_segments:
        sub_segments = segment_block(segment, '\n\n')
        for sub_segment in sub_segments:
#             print(sub_segment)
            trimmed_segments.append(sub_segment)
            
    # Add up blocks to make each of them the maximum size that's still under the max_length limit
    # Uses greedy to add up
    # if single block is too big, subsegment using single \n
    # if newlines don't work, subsegment using white space
    # if none works, chop the blocks disregarding anything
    maxed_segments = []
    cumulated_segment = {}
    cumulated_length = 0
    for segment in trimmed_segments:
        current_length = get_block_length(segment)
            
        # if segment too long, subsegment using newline
        if current_length >= max_length:
            sub_segments = segment_block(segment, '\n')
            
            for sub_segment in sub_segments:
                current_length = get_block_length(sub_segment)
                
                # if segment too long, subsegment using space
                if current_length >= max_length:
                    sub2_segments = segment_block(sub_segment, ' ')
                    
                    for sub2_segment in sub2_segments:
                        current_length = get_block_length(sub2_segment)
                        
                        # if segment too long, subsegment disregarding whitespaces
                        if current_length >= max_length:
                            sub3_segments = segment_block_by_length(sub2_segment, max_length)
                            for sub3_segment in sub3_segments:
                                current_length = get_block_length(sub3_segment)
                                maxed_segments.append(sub3_segment)
                                
                        # check if previous segment in the final list still have space to append current block
                        elif len(maxed_segments) > 0:
                            if maxed_segments[-1]['node_type'] != sub2_segment['node_type']:
                                maxed_segments.append(sub2_segment)
                            elif get_merged_block_length(maxed_segments[-1], sub2_segment) <= max_length:
                                maxed_segments[-1] = (merge_block(maxed_segments[-1], sub2_segment))
                            else:
                                maxed_segments.append(sub2_segment)
                        else:
                            maxed_segments.append(sub2_segment)
                            
                # check if previous segment in the final list still have space to append current block
                elif len(maxed_segments) > 0:
                    if maxed_segments[-1]['node_type'] != sub_segment['node_type']:
                        maxed_segments.append(sub_segment)
                    elif get_merged_block_length(maxed_segments[-1], sub_segment) <= max_length:
                        maxed_segments[-1] = (merge_block(maxed_segments[-1], sub_segment))
                    else:
                        maxed_segments.append(sub_segment)
                else:
                    maxed_segments.append(sub_segment)
                    
        # check if previous segment in the final list still have space to append current block
        elif len(maxed_segments) > 0:
            if maxed_segments[-1]['node_type'] != segment['node_type']:
                maxed_segments.append(segment)
            elif get_merged_block_length(maxed_segments[-1], segment) <= max_length:
                maxed_segments[-1] = (merge_block(maxed_segments[-1], segment))
            else:
                maxed_segments.append(segment)
        else:
            maxed_segments.append(segment)
            
    return maxed_segments

def segments_to_text(segments):
    text_list = []
    for segment in segments:
        if segment['node_type'] == 'QUOTE_BLOCK':
            text_list.append('> ' + segment['text_content'])
        elif segment['node_type'] == 'CODE_BLOCK':
            text_list.append('```' + segment['code_lang'] + '\n' + segment['text_content'] + '```')
        else:
            text_list.append(segment['text_content'])
    return text_list

def markdown_to_text(markdown, max_length):
    text_list = segments_to_text(segment_markdown(markdown, max_length))
    merged_text_list = []
    merged_idx = 0
    for idx, text in enumerate(text_list):
        if idx == 0:
            merged_text_list.append(text)
            merged_idx += 1
        else:
            if len(merged_text_list[merged_idx - 1]) + len(text) < max_length:
                merged_text_list[merged_idx - 1] = merged_text_list[merged_idx - 1] + text
            else:
                merged_text_list.append(text)
                merged_idx += 1
    return merged_text_list