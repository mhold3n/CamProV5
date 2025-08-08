#include "../include/CamAnimation.h"
#include <cmath>
#include <iostream>
#include <algorithm>

// Vertex shader source code
const char* vertexShaderSource = R"(
    #version 330 core
    layout(location = 0) in vec2 position;
    uniform mat4 transform;
    uniform vec4 color;
    out vec4 fragColor;
    
    void main() {
        gl_Position = transform * vec4(position, 0.0, 1.0);
        fragColor = color;
    }
)";

// Fragment shader source code
const char* fragmentShaderSource = R"(
    #version 330 core
    in vec4 fragColor;
    out vec4 outColor;
    
    void main() {
        outColor = fragColor;
    }
)";

CamAnimation::CamAnimation()
    : m_frameBuffer(0)
    , m_renderTexture(0)
    , m_shaderProgram(0)
    , m_vertexBuffer(0)
    , m_indexBuffer(0)
    , m_currentFrame(0)
    , m_numFrames(100)
    , m_paused(true)
    , m_n(1.0f)
    , m_stroke(0.0f)
    , m_tdcOffset(0.0f)
    , m_outerBoundaryRadius(0.0f)
    , m_rodLength(0.0f)
    , m_cycleRatio(1.0f)
    , m_width(0)
    , m_height(0)
{
}

CamAnimation::~CamAnimation() {
    cleanup();
}

bool CamAnimation::initialize(int width, int height) {
    m_width = width;
    m_height = height;
    
    // Initialize GLFW
    if (!glfwInit()) {
        std::cerr << "Failed to initialize GLFW" << std::endl;
        return false;
    }
    
    // Configure GLFW
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    
    // Create an invisible window for OpenGL context
    GLFWwindow* window = glfwCreateWindow(1, 1, "", nullptr, nullptr);
    if (!window) {
        std::cerr << "Failed to create GLFW window" << std::endl;
        glfwTerminate();
        return false;
    }
    
    // Make the window's context current
    glfwMakeContextCurrent(window);
    
    // Initialize GLEW
    glewExperimental = GL_TRUE;
    if (glewInit() != GLEW_OK) {
        std::cerr << "Failed to initialize GLEW" << std::endl;
        glfwDestroyWindow(window);
        glfwTerminate();
        return false;
    }
    
    // Setup framebuffer and texture for offscreen rendering
    glGenFramebuffers(1, &m_frameBuffer);
    glBindFramebuffer(GL_FRAMEBUFFER, m_frameBuffer);
    
    glGenTextures(1, &m_renderTexture);
    glBindTexture(GL_TEXTURE_2D, m_renderTexture);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, m_renderTexture, 0);
    
    // Check if framebuffer is complete
    if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) {
        std::cerr << "Framebuffer is not complete" << std::endl;
        cleanup();
        glfwDestroyWindow(window);
        glfwTerminate();
        return false;
    }
    
    // Setup shaders and buffers
    setupShaders();
    setupBuffers();
    
    // Unbind framebuffer
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    
    // Destroy the temporary window
    glfwDestroyWindow(window);
    
    return true;
}

void CamAnimation::updateData(
    const std::vector<float>& baseCamTheta,
    const std::vector<float>& baseCamR,
    const std::vector<float>& baseCamX,
    const std::vector<float>& baseCamY,
    const std::vector<float>& phiArray,
    const std::vector<float>& centerRArray,
    float n,
    float stroke,
    float tdcOffset,
    const std::vector<float>& innerEnvelopeTheta,
    const std::vector<float>& innerEnvelopeR,
    float outerBoundaryRadius,
    float rodLength,
    float cycleRatio
) {
    // Store animation data
    m_baseCamTheta = baseCamTheta;
    m_baseCamR = baseCamR;
    m_baseCamX = baseCamX;
    m_baseCamY = baseCamY;
    m_phiArray = phiArray;
    m_centerRArray = centerRArray;
    m_innerEnvelopeTheta = innerEnvelopeTheta;
    m_innerEnvelopeR = innerEnvelopeR;
    
    // Store parameters
    m_n = n;
    m_stroke = stroke;
    m_tdcOffset = tdcOffset;
    m_outerBoundaryRadius = outerBoundaryRadius;
    m_rodLength = rodLength;
    m_cycleRatio = cycleRatio;
    
    // Update number of frames based on phi array size
    m_numFrames = static_cast<int>(phiArray.size());
    
    // Reset animation
    reset();
}

void CamAnimation::render() {
    if (!m_paused) {
        m_currentFrame = (m_currentFrame + 1) % m_numFrames;
    }
    
    glBindFramebuffer(GL_FRAMEBUFFER, m_frameBuffer);
    glViewport(0, 0, m_width, m_height);
    
    // Clear the framebuffer
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    
    // Use the shader program
    glUseProgram(m_shaderProgram);
    
    // Calculate current phi and rCenter based on frame
    float phi = 0.0f;
    float rCenter = 0.0f;
    
    if (!m_phiArray.empty() && !m_centerRArray.empty()) {
        phi = m_phiArray[m_currentFrame % m_phiArray.size()];
        rCenter = m_centerRArray[m_currentFrame % m_centerRArray.size()];
    }
    
    // Calculate cam world state
    calculateCamWorldState(phi, rCenter, m_n);
    
    // Draw animation elements
    drawEnvelope();
    drawCamProfile();
    drawRod();
    
    // Unbind framebuffer
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
}

void CamAnimation::play() {
    m_paused = false;
}

void CamAnimation::pause() {
    m_paused = true;
}

void CamAnimation::reset() {
    m_currentFrame = 0;
    m_paused = true;
}

void CamAnimation::setCurrentFrame(int frame) {
    m_currentFrame = std::max(0, std::min(frame, m_numFrames - 1));
}

int CamAnimation::getCurrentFrame() const {
    return m_currentFrame;
}

GLuint CamAnimation::getTextureId() const {
    return m_renderTexture;
}

void CamAnimation::setupShaders() {
    // Create vertex shader
    GLuint vertexShader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertexShader, 1, &vertexShaderSource, nullptr);
    glCompileShader(vertexShader);
    
    // Check vertex shader compilation
    GLint success;
    GLchar infoLog[512];
    glGetShaderiv(vertexShader, GL_COMPILE_STATUS, &success);
    if (!success) {
        glGetShaderInfoLog(vertexShader, 512, nullptr, infoLog);
        std::cerr << "Vertex shader compilation failed: " << infoLog << std::endl;
    }
    
    // Create fragment shader
    GLuint fragmentShader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragmentShader, 1, &fragmentShaderSource, nullptr);
    glCompileShader(fragmentShader);
    
    // Check fragment shader compilation
    glGetShaderiv(fragmentShader, GL_COMPILE_STATUS, &success);
    if (!success) {
        glGetShaderInfoLog(fragmentShader, 512, nullptr, infoLog);
        std::cerr << "Fragment shader compilation failed: " << infoLog << std::endl;
    }
    
    // Create shader program
    m_shaderProgram = glCreateProgram();
    glAttachShader(m_shaderProgram, vertexShader);
    glAttachShader(m_shaderProgram, fragmentShader);
    glLinkProgram(m_shaderProgram);
    
    // Check shader program linking
    glGetProgramiv(m_shaderProgram, GL_LINK_STATUS, &success);
    if (!success) {
        glGetProgramInfoLog(m_shaderProgram, 512, nullptr, infoLog);
        std::cerr << "Shader program linking failed: " << infoLog << std::endl;
    }
    
    // Delete shaders (they're linked into the program now)
    glDeleteShader(vertexShader);
    glDeleteShader(fragmentShader);
}

void CamAnimation::setupBuffers() {
    // Create vertex buffer
    glGenBuffers(1, &m_vertexBuffer);
    
    // Create index buffer
    glGenBuffers(1, &m_indexBuffer);
}

void CamAnimation::calculateCamWorldState(float phi, float rCenter, float n) {
    // This method would calculate the current state of the cam based on the input parameters
    // For now, it's a placeholder
}

void CamAnimation::drawCamProfile() {
    // This method would draw the cam profile using the shader program and vertex buffer
    // For now, it's a placeholder
    
    // Example of drawing a simple circle as a placeholder
    const int numSegments = 100;
    std::vector<float> vertices;
    
    // Generate circle vertices
    for (int i = 0; i < numSegments; ++i) {
        float theta = 2.0f * 3.14159f * static_cast<float>(i) / static_cast<float>(numSegments);
        float x = 0.5f * cosf(theta);
        float y = 0.5f * sinf(theta);
        vertices.push_back(x);
        vertices.push_back(y);
    }
    
    // Bind vertex buffer
    glBindBuffer(GL_ARRAY_BUFFER, m_vertexBuffer);
    glBufferData(GL_ARRAY_BUFFER, vertices.size() * sizeof(float), vertices.data(), GL_DYNAMIC_DRAW);
    
    // Set up vertex attributes
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), (void*)0);
    
    // Set uniform values
    GLint transformLoc = glGetUniformLocation(m_shaderProgram, "transform");
    GLint colorLoc = glGetUniformLocation(m_shaderProgram, "color");
    
    // Identity matrix for transform
    float transform[16] = {
        1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 1.0f
    };
    
    // Set color to red
    float color[4] = { 1.0f, 0.0f, 0.0f, 1.0f };
    
    glUniformMatrix4fv(transformLoc, 1, GL_FALSE, transform);
    glUniform4fv(colorLoc, 1, color);
    
    // Draw the circle
    glDrawArrays(GL_LINE_LOOP, 0, numSegments);
    
    // Disable vertex attributes
    glDisableVertexAttribArray(0);
}

void CamAnimation::drawEnvelope() {
    // This method would draw the envelope using the shader program and vertex buffer
    // For now, it's a placeholder
}

void CamAnimation::drawRod() {
    // This method would draw the connecting rod using the shader program and vertex buffer
    // For now, it's a placeholder
}

void CamAnimation::cleanup() {
    // Delete OpenGL resources
    if (m_frameBuffer != 0) {
        glDeleteFramebuffers(1, &m_frameBuffer);
        m_frameBuffer = 0;
    }
    
    if (m_renderTexture != 0) {
        glDeleteTextures(1, &m_renderTexture);
        m_renderTexture = 0;
    }
    
    if (m_shaderProgram != 0) {
        glDeleteProgram(m_shaderProgram);
        m_shaderProgram = 0;
    }
    
    if (m_vertexBuffer != 0) {
        glDeleteBuffers(1, &m_vertexBuffer);
        m_vertexBuffer = 0;
    }
    
    if (m_indexBuffer != 0) {
        glDeleteBuffers(1, &m_indexBuffer);
        m_indexBuffer = 0;
    }
    
    // Terminate GLFW
    glfwTerminate();
}