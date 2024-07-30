cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(EvoSeg)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/DeepInsightData/EvoSeg")
set(EXTENSION_CONTRIBUTORS "Longhao Cao (DeepInsightData)")
set(EXTENSION_DESCRIPTION "Evolution Segmentation")
set(EXTENSION_ICONURL "https://github.com/DeepInsightData/EvoSeg/main/EvoSeg.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/DeepInsightData/EvoSeg/main/Screenshots/1.png")
set(EXTENSION_DEPENDS "PyTorch") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(EvoSeg)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
