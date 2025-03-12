local patchScript = ...  -- Get the patch script passed from main.lua

local patchChannel = love.thread.getChannel("patch_output")  -- Channel for output communication

-- Function to execute the patching process
local function runPatch()
    local process = io.popen(patchScript)  

    while true do
        local line = process:read("*line")  -- Read output line by line
        if not line then
            break  -- Exit the loop if no more output
        end
        patchChannel:push(line)  -- Push the output to the channel
    end

    local exitCode = process:close() 

    -- Always notify success after the patch script has completed.
    patchChannel:push("Patching completed successfully!") 
end

runPatch() 