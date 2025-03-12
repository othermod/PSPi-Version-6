-- Load the timer module
local Timer = require "timer"



-- Screen dimensions and global scale factor
local screenWidth, screenHeight
local scaleFactor

-- Colors for drawing
local seaColor = {79 / 255, 168 / 255, 221 / 255}  -- Sea color
local skyColor = {78 / 255, 190 / 255, 238 / 255}  -- Sky color
local reflectionColor = {245 / 255, 168 / 255, 108 / 255}  -- Reflection color
local sunColor = {243 / 255, 149 / 255, 23 / 255}  -- Sun color

-- Entities and resources
local sun = {}
local boat = {}
local reflection = {}
local logo = {}
local text = {}
local blackhole = {}
local boatImage
local logoShader

-- Wait for signal
local fileCheckInterval = 0.5  -- Check every 0.5 seconds
local timeSinceLastCheck = -2.25  -- wait 2.0 seconds before checking for the file
local fileFound = false


-- Function declarations
local drawSky, drawSun, drawSea, drawBoat, drawReflection, drawLogo, drawText

-- Screen and scaling initialization
local function initializeScreen()
    screenWidth, screenHeight = love.graphics.getDimensions()
    local referenceHeight = 600
    scaleFactor = screenHeight / referenceHeight
end


local function initializeBlackHole()
    blackhole = {
        x = screenWidth / 2,
        y = screenHeight / 2,
        radius = 0,
        maxRadius = math.sqrt(screenWidth^2 + screenHeight^2),
        color = {0, 0, 0}
    }

    -- Expand the black hole on startup
    Timer.after(0.3, function()
        Timer.tween(0.5, blackhole, {radius = blackhole.maxRadius}, 'in-cubic')
    end)
end



local function startBlackHoleClose()
    -- Scale down the text with black hole animation
    Timer.tween(0.5, text, {scale = 0}, 'in-back')

    -- Wait 0.5 seconds, then run the black hole animation
    Timer.after(0.5, function()
        Timer.tween(0.5, blackhole, {radius = 0}, 'out-cubic')

        -- After the black hole animation, delete the file and quit
        Timer.after(0.5, function()
            -- Detect the path where main.lua is located
            local mainPath = love.filesystem.getSource()
            local filePath = mainPath .. "/stopsplash"  -- Construct full path to 'stopsplash'

            print("Attempting to delete file at path: " .. filePath)

            -- Use os.remove directly
            local success, err = os.remove(filePath)
            if success then
                print("File 'stopsplash' deleted successfully.")
            else
                print("Failed to delete file: ", err)
            end

            -- Quit the game
            love.event.quit()
        end)
    end)
end






-- Sun initialization
local function initializeSun()
    sun = {
        x = screenWidth / 2,
        y = screenHeight / 2,
        radius = 0,
        color = sunColor
    }
   
    Timer.after(0.6, function()
        Timer.tween(0.5, sun, {radius = 150 * scaleFactor}, 'out-cubic')
    end)
end

-- Boat initialization
local function initializeBoat()
    boat = {
        scale = 0,
        y = 0,
        wobble = 0,
        wobbleSpeed = 3,
        wobbleAmplitude = 3,
        offset = 10 * scaleFactor
    }

    Timer.after(0.4, function()
        Timer.tween(1, boat, {scale = 0.4 * scaleFactor}, 'out-cubic')
    end)

    Timer.every(0.016, function()
        boat.wobble = boat.wobble + boat.wobbleSpeed * 0.016
    end)
end

-- Reflection initialization
local function initializeReflection()
    reflection = {
        height = 0,
        noise = 1,
        waveFrequency = 0.1,
        waveSpeed = 0.03
    }
end

-- Logo initialization
local function initializeLogo()
    logo = {
        sprite = love.graphics.newImage("assets/logo.png"),
        mask = love.graphics.newImage("assets/logo-mask.png"),
        pen = 0,
        color = {0, 0, 0},  -- Default color for the logo (black)
        x = 0.5,  -- Horizontal position as a percentage of screen width
        y = 0.75,  -- Vertical position as a percentage of screen height
        scale = 0.3 * scaleFactor  -- Scale factor for the logo
    }

    logoShader = love.graphics.newShader([[ 
        extern number pen;
        extern Image mask;

        vec4 effect(vec4 color, Image logo, vec2 tc, vec2 sc)
        {
            number value = max(Texel(mask, tc).r, max(Texel(mask, tc).g, Texel(mask, tc).b));
            number alpha = Texel(mask, tc).a;

            if (alpha > 0.0) {
                if (pen >= value) {
                    return color * Texel(logo, tc);
                }
            }
            return vec4(0);
        }
    ]])
    Timer.after(1, function()
        Timer.tween(2, logo, {pen = 1}, 'out-quart')  -- Gradually reveal the logo over 2 seconds
    
    end)
end

-- Initialize text with zoom-in effect but keep it visible until signal
local function initializeText()
    local fontSize = 32 * scaleFactor  -- Scale font size dynamically based on scaleFactor
    text = {
        content = "Your Ultimate Handheld Linux Port Manager",
        font = love.graphics.newFont("assets/Aero Matics Regular.ttf", fontSize),  -- Use scaled font size
        color = {0, 0, 0},  -- Default text color
        x = 0.5,  -- Horizontal position as percentage of screen width (centered)
        y = 0.9,  -- Vertical position as percentage of screen height (below the logo)
        scale = 0  -- Start with no scale (invisible)
    }

    -- Zoom in the text over 1.2 seconds
    Timer.after(1.8, function()
        Timer.tween(0.5, text, {scale = 1}, 'out-back')  -- Only scale position, font size is pre-scaled
    end)
end


function love.load()
    local desktopWidth, desktopHeight = love.window.getDesktopDimensions()
    love.window.setMode(desktopWidth, desktopHeight, {fullscreen = true, fullscreentype = "desktop"})
    love.graphics.setDefaultFilter("nearest", "nearest")
    initializeScreen()
    initializeSun()
    initializeBoat()
    initializeReflection()
    initializeLogo()
    initializeText()
    initializeBlackHole()
    boatImage = love.graphics.newImage("assets/boat.png")
end

-- Draw the sky
function drawSky()
    love.graphics.setColor(skyColor)
    love.graphics.rectangle("fill", 0, 0, screenWidth, screenHeight / 2)
end

-- Draw the sun
function drawSun()
    love.graphics.setColor(sun.color)
    love.graphics.circle("fill", sun.x, sun.y, sun.radius)
end

-- Draw the sea
function drawSea()
    love.graphics.setColor(seaColor)
    love.graphics.rectangle("fill", 0, screenHeight / 2, screenWidth, screenHeight / 2)
end

-- Draw the boat
function drawBoat()
    local scaledBoatWidth = boatImage:getWidth() * boat.scale
    local scaledBoatHeight = boatImage:getHeight() * boat.scale
    local boatX = (screenWidth / 2) - (scaledBoatWidth / 2)

    local seaTop = screenHeight / 2
    local boatYBase = seaTop - scaledBoatHeight + boat.offset
    local maxWobble = math.min(boat.wobbleAmplitude * scaleFactor, scaledBoatHeight / 2)
    local wobbleOffset = maxWobble * math.sin(boat.wobble)

    local boatY = boatYBase + wobbleOffset

    love.graphics.setColor(1, 1, 1)
    love.graphics.draw(boatImage, boatX, boatY, 0, boat.scale, boat.scale)
end

-- Draw the reflection
function drawReflection()
    local yStart = screenHeight / 2
    local reflectionRadius = sun.radius - 20 * scaleFactor  -- Scale reflection based on screen height

    for y = yStart + reflection.height, yStart + reflection.height + reflectionRadius do
        local baseWidth = math.sqrt(reflectionRadius ^ 2 - (y - (yStart + reflection.height)) ^ 2)
        local leftAmplitude = love.math.noise(y * 0.15 + reflection.noise) * 80 * scaleFactor
        local rightAmplitude = love.math.noise(y * 0.2 + reflection.noise) * 80 * scaleFactor

        local leftX = sun.x - baseWidth + math.sin(y * reflection.waveFrequency) * leftAmplitude
        local rightX = sun.x + baseWidth - math.sin(y * reflection.waveFrequency) * rightAmplitude

        love.graphics.setColor(reflectionColor)
        love.graphics.line(leftX, y, rightX, y)
    end

    reflection.noise = reflection.noise + reflection.waveSpeed
end

-- Draw the logo
function drawLogo()
    local logoWidth, logoHeight = logo.sprite:getDimensions()
    local logoScale = logo.scale

    love.graphics.setShader(logoShader)
    logoShader:send("mask", logo.mask)
    logoShader:send("pen", logo.pen)

    love.graphics.setColor(logo.color)  -- Use the color defined in the logo table

    -- Draw the logo with its x and y position as percentages of screen dimensions
    love.graphics.draw(
        logo.sprite,
        (screenWidth - logoWidth * logoScale) * logo.x,  -- Use logo.x as percentage for x position
        (screenHeight - logoHeight * logoScale) * logo.y,  -- Use logo.y as percentage for y position
        0, logoScale, logoScale
    )

    love.graphics.setShader()
    love.graphics.setColor(1, 1, 1)
end

-- Draw the text with zoom effect
function drawText()
    love.graphics.setFont(text.font)
    love.graphics.setColor(text.color)

    local textWidth = text.font:getWidth(text.content)
    local textHeight = text.font:getHeight(text.content)

    -- Calculate the position, keeping the text centered while scaling
    local scaledX = (screenWidth - textWidth * text.scale) * text.x
    local scaledY = (screenHeight - textHeight * text.scale) * text.y

    -- Apply scaling transformation
    love.graphics.push()  -- Save current transformation state
    love.graphics.translate(scaledX + (textWidth * text.scale) / 2, scaledY + (textHeight * text.scale) / 2)
    love.graphics.scale(text.scale)
    love.graphics.translate(-(textWidth / 2), -(textHeight / 2))
    love.graphics.print(text.content, 0, 0)
    love.graphics.pop()  -- Restore the original transformation state
end

-- Draw the black hole effect
local function drawBlackHole()
    love.graphics.setColor(blackhole.color)

    -- Use a stencil to create the black hole effect
    love.graphics.stencil(function()
        love.graphics.circle("fill", blackhole.x, blackhole.y, blackhole.radius)
    end, "replace", 1)

    -- Enable the stencil test to draw outside the circle
    love.graphics.setStencilTest("less", 1)

    -- Draw the black screen
    love.graphics.rectangle("fill", 0, 0, screenWidth, screenHeight)

    -- Reset the stencil test
    love.graphics.setStencilTest()
end


function love.draw()
    drawSky()
    drawSun()
    drawBoat()
    drawSea()
    drawReflection()
    drawLogo()
    drawText()
    drawBlackHole()
end

local function checkFileSignal(dt)
    timeSinceLastCheck = timeSinceLastCheck + dt

    if timeSinceLastCheck >= fileCheckInterval then
        timeSinceLastCheck = 0  -- Reset the timer

        if love.filesystem.getInfo("stopsplash") then
            fileFound = true
            startBlackHoleClose()  -- Start the black hole animation when file is found
        end
    end
end

-- Update game state
function love.update(dt)
    Timer.update(dt)
    checkFileSignal(dt)  -- Clean file check call
end
