#pragma once

#include <vector>
#include <GL/glew.h>
#include <GLFW/glfw3.h>

/**
 * CamAnimation class
 * Provides high-performance 2D animations of FEA results using OpenGL
 */
class CamAnimation {
public:
    CamAnimation();
    ~CamAnimation();
    
    /**
     * Initialize OpenGL context and resources
     * @param width Width of the rendering surface
     * @param height Height of the rendering surface
     * @return True if initialization was successful, false otherwise
     */
    bool initialize(int width, int height);
    
    /**
     * Update animation data
     * @param baseCamTheta Array of theta values for the base cam profile
     * @param baseCamR Array of radius values for the base cam profile
     * @param baseCamX Array of X coordinates for the base cam profile
     * @param baseCamY Array of Y coordinates for the base cam profile
     * @param phiArray Array of phi values for animation
     * @param centerRArray Array of center radius values for animation
     * @param n Cam profile parameter
     * @param stroke Stroke length
     * @param tdcOffset Top dead center offset
     * @param innerEnvelopeTheta Array of theta values for inner envelope
     * @param innerEnvelopeR Array of radius values for inner envelope
     * @param outerBoundaryRadius Radius of outer boundary
     * @param rodLength Length of connecting rod
     * @param cycleRatio Ratio of cycle
     */
    void updateData(
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
    );
    
    /**
     * Render current frame
     * Updates the animation state and renders the current frame
     */
    void render();
    
    /**
     * Start playing the animation
     */
    void play();
    
    /**
     * Pause the animation
     */
    void pause();
    
    /**
     * Reset the animation to the first frame
     */
    void reset();
    
    /**
     * Set the current frame of the animation
     * @param frame Frame index
     */
    void setCurrentFrame(int frame);
    
    /**
     * Get the current frame of the animation
     * @return Current frame index
     */
    int getCurrentFrame() const;
    
    /**
     * Get the OpenGL texture ID for the animation
     * @return OpenGL texture ID
     */
    GLuint getTextureId() const;
    
private:
    // OpenGL resources
    GLuint m_frameBuffer;
    GLuint m_renderTexture;
    GLuint m_shaderProgram;
    GLuint m_vertexBuffer;
    GLuint m_indexBuffer;
    
    // Animation data
    std::vector<float> m_baseCamTheta;
    std::vector<float> m_baseCamR;
    std::vector<float> m_baseCamX;
    std::vector<float> m_baseCamY;
    std::vector<float> m_phiArray;
    std::vector<float> m_centerRArray;
    std::vector<float> m_innerEnvelopeTheta;
    std::vector<float> m_innerEnvelopeR;
    
    // Animation state
    int m_currentFrame;
    int m_numFrames;
    bool m_paused;
    
    // Cam parameters
    float m_n;
    float m_stroke;
    float m_tdcOffset;
    float m_outerBoundaryRadius;
    float m_rodLength;
    float m_cycleRatio;

    // Rendering dimensions
    int m_width;
    int m_height;

    // Calculated geometry for current frame
    std::vector<float> m_camWorldVertices;      // x,y pairs of cam profile
    std::vector<float> m_envelopeWorldVertices; // x,y pairs of envelope
    std::vector<float> m_rodVertices;           // line vertices for connecting rod
    
    // Helper methods
    void setupShaders();
    void setupBuffers();
    void calculateCamWorldState(float phi, float rCenter, float n);
    void drawCamProfile();
    void drawEnvelope();
    void drawRod();
    void cleanup();
};