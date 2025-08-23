import pymysql
import os
from dotenv import load_dotenv

# --- 1. 数据库配置 (自动加载 .env 文件) ---

def load_db_config_from_env():
    """从项目特定位置的 .env 文件加载数据库配置"""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(project_root, 'middleware', '.env')

        if os.path.exists(env_path):
            print(f"🔍 正在从 '{env_path}' 加载环境变量...")
            load_dotenv(dotenv_path=env_path)
        else:
            print(f"⚠️ 警告: 未在 '{env_path}' 找到 .env 文件，将使用默认值或全局环境变量。")

        db_config = {
            "host": os.getenv("HEADER_ADDRESS", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", 3306)),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("MYSQL_ROOT_PASSWORD"),
            "db": os.getenv("DB_NAME", "agent_db"),
            "charset": "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
        }
        
        if not db_config["password"]:
            print("❌ 错误: 未能从 .env 文件或环境变量中加载 MYSQL_ROOT_PASSWORD。")
            return None
            
        return db_config

    except Exception as e:
        print(f"❌ 加载配置时发生错误: {e}")
        return None

DB_CONFIG = load_db_config_from_env()

# --- 2. 各表的 CREATE TABLE 语句 ---

def create_users_table(cursor):
    """创建用户表 (users)"""
    # ... (此函数保持不变)
    sql = """
    CREATE TABLE IF NOT EXISTS `users` (
        `user_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户唯一ID，主键',
        `student_no` VARCHAR(255) UNIQUE COMMENT '学号，唯一约束，可为空',
        `name` VARCHAR(255) NOT NULL COMMENT '用户姓名或昵称',
        `gender` ENUM('male', 'female', 'other') NOT NULL COMMENT '性别',
        `age` INT COMMENT '年龄',
        `role` VARCHAR(50) NOT NULL COMMENT '用户角色 (e.g., student, teacher, admin)',
        `permissions` JSON COMMENT '用户的权限列表，以JSON格式存储',
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(sql)
    print("✅ Table 'users' created successfully.")


def create_problems_table(cursor):
    """创建题目表 (problems)"""
    # ... (此函数保持不变)
    sql = """
    CREATE TABLE IF NOT EXISTS `problems` (
        `problem_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '题目唯一ID，主键',
        `problem_code` VARCHAR(255) NOT NULL UNIQUE COMMENT '题目的业务标识 (e.g., SDUOJ-1204)，唯一约束',
        `title` VARCHAR(255) NOT NULL COMMENT '题目名称',
        `full_markdown_description` MEDIUMTEXT COMMENT '从OJ获取的完整Markdown格式题目描述',
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录最后更新时间'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(sql)
    print("✅ Table 'problems' created successfully.")


def create_problem_analysis_assets_table(cursor):
    """(核心修改) 创建题目分析资产表，直接存储内容"""
    sql = """
    CREATE TABLE IF NOT EXISTS `problem_analysis_assets` (
        `asset_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '资产记录唯一ID，主键',
        `problem_id` INT NOT NULL UNIQUE COMMENT '外键，关联到 problems.problem_id',
        `simplified_problem_content` MEDIUMTEXT COMMENT '直接存储 problem_s.md (简化题面) 的完整内容',
        `solution_collection_content` MEDIUMTEXT COMMENT '直接存储 solve.md (题解集合) 的完整内容',
        `error_collection_content` MEDIUMTEXT COMMENT '直接存储 error.md (错误集合) 的完整内容',
        `input_checker_code` MEDIUMTEXT COMMENT '直接存储 input_checker.py (数据校验器) 的源代码',
        `edge_cases_content` MEDIUMTEXT COMMENT '直接存储 edge_test_gen.py 的产出物或其源代码',
        `last_analyzed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '资产最后更新时间',
        FOREIGN KEY (`problem_id`) REFERENCES `problems`(`problem_id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(sql)
    print("✅ Table 'problem_analysis_assets' (内容直存版) created successfully.")

def create_student_submissions_table(cursor):
    """创建学生提交表 (student_submissions)"""
    # ... (此函数保持不变)
    sql = """
    CREATE TABLE IF NOT EXISTS `student_submissions` (
        `submission_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '提交记录唯一ID，主键',
        `user_id` INT NOT NULL COMMENT '提交者ID，外键关联 users.user_id',
        `problem_id` INT NOT NULL COMMENT '题目ID，外键关联 problems.problem_id',
        `code` MEDIUMTEXT NOT NULL COMMENT '用户提交的完整源代码',
        `language` VARCHAR(50) NOT NULL COMMENT '提交所用的编程语言 (e.g., C++14)',
        `judge_result` JSON COMMENT '来自OJ的评测结果，以JSON格式存储',
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
        `fence` BIGINT NOT NULL COMMENT '并发控制Fencing Token，用于防止旧任务写入',
        FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
        FOREIGN KEY (`problem_id`) REFERENCES `problems`(`problem_id`) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(sql)
    print("✅ Table 'student_submissions' created successfully.")

    
def create_error_analysis_table(cursor):
    """创建错误分析表 (error_analysis)"""
    # ... (此函数保持不变)
    sql = """
    CREATE TABLE IF NOT EXISTS `error_analysis` (
        `analysis_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '错误分析记录唯一ID，主键',
        `submission_id` INT NOT NULL UNIQUE COMMENT '关联的提交ID，外键，唯一约束',
        `user_id` INT NOT NULL COMMENT '用户ID，外键，用于快速查询',
        `problem_id` INT NOT NULL COMMENT '题目ID，外键，用于快速查询',
        `error_type` ENUM('conceptual', 'implementation', 'timeout', 'unknown') COMMENT '由LLM判断的错误分类',
        `algorithm_analysis` TEXT COMMENT '对代码所用算法和核心思路的分析',
        `detailed_reasoning` TEXT COMMENT '详细的错误原因解释',
        `fix_suggestion` TEXT COMMENT '具体的修复建议或修正后的代码片段',
        `counter_example_input` TEXT COMMENT '针对概念性错误生成的反例输入',
        `counter_example_output` TEXT COMMENT '反例的正确输出',
        `complexity_analysis` VARCHAR(255) COMMENT '针对超时的算法时间/空间复杂度分析',
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分析记录创建时间',
        `fence` BIGINT NOT NULL COMMENT '并发控制Fencing Token',
        FOREIGN KEY (`submission_id`) REFERENCES `student_submissions`(`submission_id`) ON DELETE CASCADE,
        FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE,
        FOREIGN KEY (`problem_id`) REFERENCES `problems`(`problem_id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(sql)
    print("✅ Table 'error_analysis' created successfully.")


def create_interaction_logs_table(cursor):
    """创建交互日志表 (interaction_logs)"""
    # ... (此函数保持不变)
    sql = """
    CREATE TABLE IF NOT EXISTS `interaction_logs` (
        `log_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '交互日志唯一ID，主键',
        `user_id` INT NOT NULL COMMENT '参与交互的用户ID，外键',
        `input` TEXT COMMENT '用户输入的内容',
        `output` MEDIUMTEXT COMMENT '系统的响应内容',
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '交互发生时间',
        FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(sql)
    print("✅ Table 'interaction_logs' created successfully.")


def create_task_status_table(cursor):
    """创建任务状态表 (task_status)"""
    # ... (此函数保持不变)
    sql = """
    CREATE TABLE IF NOT EXISTS `task_status` (
        `task_id` VARCHAR(255) PRIMARY KEY COMMENT '任务的全局唯一ID，由AgentHub核心框架生成',
        `user_id` INT COMMENT '任务发起者ID，外键',
        `problem_id` INT COMMENT '任务关联的题目ID，外键',
        `related_submission_id` INT COMMENT '任务关联的提交ID，外键',
        `task_type` VARCHAR(100) NOT NULL COMMENT '任务类型 (e.g., problem_analysis, error_diagnosis)',
        `status` ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending' COMMENT '任务当前状态',
        `start_time` DATETIME COMMENT '任务实际开始执行的时间',
        `end_time` DATETIME COMMENT '任务完成或失败的时间',
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '任务创建时间',
        `result_summary` TEXT COMMENT '任务完成后的结果摘要或失败时的错误信息',
        `fence` BIGINT NOT NULL COMMENT '并发控制Fencing Token',
        FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE SET NULL,
        FOREIGN KEY (`problem_id`) REFERENCES `problems`(`problem_id`) ON DELETE SET NULL,
        FOREIGN KEY (`related_submission_id`) REFERENCES `student_submissions`(`submission_id`) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(sql)
    print("✅ Table 'task_status' created successfully.")


# --- 3. 主执行函数 ---
def main():
    """主函数，连接数据库并创建所有表"""
    # ... (此函数保持不变)
    if not DB_CONFIG:
        print("数据库配置加载失败，程序退出。")
        return

    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print(f"🎉 成功连接到 MySQL 数据库 '{DB_CONFIG['db']}' at {DB_CONFIG['host']}:{DB_CONFIG['port']}.")
        
        with connection.cursor() as cursor:
            # 按正确的依赖顺序创建表
            create_users_table(cursor)
            create_problems_table(cursor)
            create_problem_analysis_assets_table(cursor)
            create_student_submissions_table(cursor)
            create_error_analysis_table(cursor)
            create_interaction_logs_table(cursor)
            create_task_status_table(cursor)
            
        connection.commit()
        print("\n🚀 所有数据表创建完毕，事务已提交。")

    except pymysql.MySQLError as e:
        print(f"❌ 数据库操作失败: {e}")
        if connection:
            connection.rollback()
            print("事务已回滚。")
    finally:
        if connection:
            connection.close()
            print("🔌 数据库连接已关闭。")

if __name__ == "__main__":
    main()