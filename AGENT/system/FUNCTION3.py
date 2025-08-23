"""
代码深度分析
"""
from AGENT.unit import extract_solution_from_code,generate_counter_example,analyze_implementation_error,judge_error_type
LLM_MODEL_FOR_ANALYSIS="deepseek/deepseek-chat"
def process_student_solution(problem_id: str, student_code: str, problem_desc: str, session: requests.Session, submission_history: list):
    """
    处理学生提交的错误代码。
    1. 提取解法描述
    2. 使用 LLM 判断错误类型（概念性/实现性）
    3. 如果是概念性错误：
        a. 生成反例测试用例
        b. 返回状态 "conceptual_error"，包含分析和反例
    4. 如果是实现性错误：
        a. 在 error.md 中查找相似错误
        b. 如果找到，返回已有错误信息
        c. 如果未找到：
            - 使用 LLM 分析错误
            - 将错误添加到 error.md
            - 返回分析结果
    """
    logging.info(f"--- 正在处理学生解法，题目 ID: {problem_id} ---")
    # 1. 提取解法描述 (用于知识库查询和 LLM 分析)
    solution_info = extract_solution_from_code(student_code, problem_desc)
    if not solution_info or 'description' not in solution_info:
        logging.error("❌ 无法提取解法描述。")
        return {"status": "error", "message": "解法提取失败"}

    solution_desc = solution_info['description']
    logging.info(f"📝 提取的解法描述: {solution_desc}")
    #2.llm 判断错误类型
    error_analysis = judge_error_type(problem_desc, student_code, LLM_MODEL_FOR_ANALYSIS)
    if error_analysis["error_type"] == "conceptual":
        logging.info("💡 判定为概念性错误。")
        counter_example_info = generate_counter_example(
            problem_desc, student_code, error_analysis, LLM_MODEL_FOR_ANALYSIS
        )
        submission_history.append({
            "code": student_code,
            "thought": "概念性错误",
            "error_info": error_analysis["reasoning"]
        })
        return {
            "status": "conceptual_error", 
            "message": f"识别到概念性错误: {error_analysis['reasoning']}",
            "analysis": error_analysis,
            "counter_example": counter_example_info
        }
    elif error_analysis["error_type"] == "implementation":
        logging.info("💡 判定为实现性错误。")
        emb = Embedding()
        embedding = emb(solution_desc).result()
        error_collection_name = "error_collection"
        vdb=VectorDB()
        top_k=5
       similar_errors = vdb(
            "search_vector",
            collection_name=error_collection_name,
            query_vector=embedding,
            top_k=top_k
        )
        if similar_errors:
            logging.info(f"✅ 在错误集中找到相似的实现性错误 (ID: {similar_errors[0]['error_id']})。")
            return {
                "status": "exists_in_kb", 
                "error_id": similar_errors[0]['error_id'],
                "message": "相似的错误已存在于错误集",
                "analysis": similar_errors[0].get('analysis', '暂无分析')
            }
        else:
            logging.info("🆕 未找到相似错误。正在使用 LLM 分析并添加到错误集。")
            
            # 使用 LLM 分析具体实现错误
            implementation_analysis = analyze_implementation_error(
                problem_desc, student_code, error_analysis, LLM_MODEL_FOR_ANALYSIS
            )
            
            # 添加到 error.md
            #FLAG 待修改 添加到mysql
            error_id = knowledge_base.add_error_sample(
                problem_id,
                solution_desc,
                student_code
            )
            
            if not error_id:
                logging.error("❌ 添加错误到错误集失败")
                return {"status": "error", "message": "添加到错误集失败"}
            
            logging.info(f"✅ 已添加实现性错误样本: {error_id}")
            
            # 记录历史
            submission_history.append({
                "code": student_code,
                "thought": "实现性错误",
                "error_info": implementation_analysis
            })
            
            return {
                "status": "implementation_error", 
                "message": f"识别到实现性错误: {implementation_analysis['implementation_analysis']}",
                "detailed_analysis": implementation_analysis['fix_suggestions'],
                "analysis": implementation_analysis,
                "error_id": error_id
            }
            
    else: # 未知错误类型
        logging.warning("❓ LLM 未能明确分类错误类型。")
        submission_history.append({
            "code": student_code,
            "thought": "未知错误类型",
            "error_info": error_analysis["reasoning"]
        })
        return {
            "status": "unknown_error", 
            "message": f"LLM未能明确分类错误类型。分析: {error_analysis['reasoning']}",
            "analysis": error_analysis
        }