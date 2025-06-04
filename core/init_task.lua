-- KEYS[1]  => task_id
-- ARGV[1]  => exec_id
-- ARGV[2]  => job (任务定义，字符串)
-- ARGV[3]  => dep (逗号分隔的依赖 exec_id 列表，字符串)

local task_key = KEYS[1]
local task_waiter_key = KEYS[2]
local exec_id  = ARGV[1]
local job_def  = ARGV[2]
local dep_str  = ARGV[3]

-- 1. 更新 job 和 dep 列表
redis.call('HSET', task_key, 'job:' .. exec_id, job_def)
redis.call('HSET', task_key, 'dep:' .. exec_id, dep_str)
--    初始化状态为 PENDING
redis.call('HSET', task_key, 'state:' .. exec_id, 'PENDING')

-- 2. 统计处于 PENDING 或 RUNNING 的依赖
local dep_cnt = 0
if dep_str ~= '' then
  for dep_id in string.gmatch(dep_str, '([^,]+)') do
    local state = redis.call('HGET', task_key, 'state:' .. dep_id)
    if state == 'PENDING' or state == 'RUNNING' then
      redis.call('SADD', task_waiter_key .. ':' .. dep_id, exec_id)
      dep_cnt = dep_cnt + 1
    end
  end
end

-- 3. 写回 dep_cnt 并返回
redis.call('HSET', task_key, 'dep_cnt:' .. exec_id, dep_cnt)
return dep_cnt
