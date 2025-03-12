-- Imports
local Talkies = require('talkies')
local push = require "push"

-- Constants
local gameWidth, gameHeight = 640, 480
local fontPath = "assets/font/PeaberryBase.ttf"
local fontSize = 16
local outputPaddingX = 24
local outputPaddingY = 12
local outputLineSpacing = 14
local outputTextColor = {0.314, 0.235, 0.482}
local spriteWidth, spriteHeight = 320, 240
local frameCount = 24
local frameRate = 12
local initialDialogDelay = 1
local gameName = "the game"
local patchTime = "5 minutes"
local patchScript = "patch_script.sh"  -- Default patch script

-- Variables
local patchOutput = {}
local patchInProgress = false
local showOutput = false
local font, cybion, spritesheet
local currentFrame = 1
local animationTimer = 0
local animationDuration = 1 / frameRate
local timer = 0
local dialogShown = false
local patchChannel = love.thread.getChannel("patch_output")  -- Channel for output 

-- Function to parse command-line arguments
local function parseCommandLineArguments()
    if arg and #arg > 0 then
        for i = 1, #arg do
            if arg[i] == "-f" and arg[i + 1] and arg[i + 1] ~= "" then
                patchScript = arg[i + 1] 
                i = i + 1 
            elseif arg[i] == "-g" and arg[i + 1] and arg[i + 1] ~= "" then
                gameName = arg[i + 1] 
                i = i + 1  
            elseif arg[i] == "-t" and arg[i + 1] and arg[i + 1] ~= "" then
                patchTime = arg[i + 1] 
                i = i + 1  
            end
        end
    end
end


-- Function to wrap text to a maximum line length
function wrapText(text, limit)
    local wrappedText = {}
    local currentLine = ""

    for word in text:gmatch("%S+") do
        if #currentLine + #word + 1 > limit then
            table.insert(wrappedText, currentLine)
            currentLine = word
        else
            currentLine = (currentLine ~= "") and (currentLine .. " " .. word) or word
        end
    end

    table.insert(wrappedText, currentLine)
    return wrappedText
end

-- Read patch output from the channel
function readPatchOutput()
    local line = patchChannel:pop()  -- Attempt to read output
    if line then
        local wrappedLines = wrapText(line, 62)
        for _, wrappedLine in ipairs(wrappedLines) do
            table.insert(patchOutput, wrappedLine)
            if #patchOutput > 4 then
                table.remove(patchOutput, 1)  -- Keep the output limited to the last 4 lines
            end
        end

        -- Check for completion
        if line:find("Patching completed successfully!") then
            patchInProgress = false
            showOutput = false
            PatchComplete() 
            return
        end
        
        -- Check for failure message
        if line:find("Patching process failed!") then
            patchInProgress = false
            showOutput = false
            PatchFailed()
            return
        end
    end
end


-- Function to start patching in a new thread
function startPatchThread()
    local thread = love.thread.newThread("patch_thread.lua")  -- Create new thread for patching
    thread:start(patchScript)  -- Pass the patch script as an argument
    patchInProgress = true
    showOutput = true
end

-- Function to show the initial Talkies dialog with two messages
function showInitialTalkiesDialog()
    Talkies.say("Cybion", "Hello! Welcome to the PortMaster patching shop. Today we will be patching " .. gameName .. " for you.", {
        image = cybion,
        thickness = 2,
        oncomplete = function()
            Talkies.say("Cybion", "The patch will take " .. patchTime .. ". So grab some coffee while you wait. Press A to start the patching process.", {
                image = cybion,
                thickness = 2,
                oncomplete = startPatchThread  -- Start the patching in a new thread
            })
        end
    })
end

-- Function to show patch complete dialog
function PatchComplete()
    Talkies.say("Cybion", "Thank you for waiting, the patching process is complete! Press A to proceed to " .. gameName .. ".", {
        thickness = 2,
        image = cybion,
        oncomplete = function()
            love.event.quit()  
        end
    })
end

-- Function to show patch failed dialog
function PatchFailed()
    Talkies.say("Cybion", "Patching failed! Please go to the PortMaster Discord for help.", {
        thickness = 2,
        image = cybion,
        oncomplete = function()
            love.event.quit()  
        end
    })
end

-- Function to initialize and start the background music
function startBackgroundMusic()
    if not altLoopSound then
        altLoopSound = love.audio.newSource("assets/sfx/Eternity.ogg", "stream")
        altLoopSound:setLooping(true)
    end
    altLoopSound:play()
end

function love.load()
    parseCommandLineArguments()

    local windowWidth, windowHeight = love.window.getDesktopDimensions()
    push:setupScreen(gameWidth, gameHeight, windowWidth, windowHeight, {
        fullscreen = false,
        resizable = true,
        pixelperfect = false,
        highdpi = true
    })
    push:setBorderColor(1, 0.859, 0.686, 1)

    font = love.graphics.newFont(fontPath, fontSize)

    -- Load assets
    cybion = love.graphics.newImage("assets/gfx/cybionImage.png")
    cybion:setFilter("nearest", "nearest")
    spritesheet = love.graphics.newImage("assets/gfx/backgroundSheet.png")
    spritesheet:setFilter("nearest", "nearest")
    patchImage = love.graphics.newImage("assets/gfx/patchImage.png")
    patchImage:setFilter("nearest", "nearest")

    Talkies.talkSound = love.audio.newSource("assets/sfx/typeSound.ogg", "static")
    Talkies.optionOnSelectSound = love.audio.newSource("assets/sfx/optionSelect.ogg", "static")
    Talkies.optionSwitchSound = love.audio.newSource("assets/sfx/optionSwitch.ogg", "static")

    -- Set Talkies configuration
    Talkies.font = font
    Talkies.characterImage = cybion
    Talkies.textSpeed = "fast"
    Talkies.inlineOptions = true
    Talkies.messageBackgroundColor = {1.000, 0.851, 0.910}
    Talkies.messageColor = outputTextColor
    Talkies.messageBorderColor = outputTextColor
    Talkies.titleColor = outputTextColor

    startBackgroundMusic()
end

-- Add a new variable for controlling the animation updates
local animationUpdateInterval = 1 / frameRate 
local animationTimer = 0 

function love.update(dt)
    Talkies.update(dt)

    -- Update animation timer every frame
    animationTimer = animationTimer + dt
    if animationTimer >= animationUpdateInterval then
        animationTimer = animationTimer - animationUpdateInterval
        currentFrame = (currentFrame % frameCount) + 1 
    end

    -- Handle dialog showing with a separate timer
    timer = timer + dt
    if not dialogShown and timer >= initialDialogDelay then
        showInitialTalkiesDialog()
        dialogShown = true
    end

    -- Read patch output from the thread
    if patchInProgress then
        readPatchOutput()  -- Check for output from the patch thread
    end
end


function love.draw()
    push:start()

    -- Draw animated spritesheet background
    local frameX = (currentFrame - 1) * spriteWidth
    local windowWidth, windowHeight = push:getWidth(), push:getHeight()
    local scaleX = windowWidth / spriteWidth
    local scaleY = windowHeight / spriteHeight

    love.graphics.draw(spritesheet, 
                       love.graphics.newQuad(frameX, 0, spriteWidth, spriteHeight, spritesheet:getDimensions()), 
                       0, 0, 0, scaleX, scaleY)

    if patchInProgress then
        love.graphics.draw(patchImage, 0, 0, 0, scaleX, scaleY)
    end

    Talkies.draw()

    if showOutput then
        love.graphics.setFont(font)
        local lineSpacing = outputLineSpacing
        local outputHeight = #patchOutput * lineSpacing
        local outputY = math.max(windowHeight - outputHeight - outputPaddingY, 0)

        for i, line in ipairs(patchOutput) do
            love.graphics.setColor(outputTextColor)
            love.graphics.print(line, outputPaddingX, outputY + (i - 1) * lineSpacing)
        end
    end

    push:finish()
end

function love.gamepadpressed(joystick, button)
    if button == "a" then
        if not patchInProgress and dialogShown then
            Talkies.onAction() 
        end
    end
end

