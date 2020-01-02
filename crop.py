from cv2 import cv2
import os
import logging
from datetime import datetime
import threading
import concurrent.futures
import numpy as np

# import matplotlib.pyplot as plt


# Global variables

numOfImagesCropped = 0
numOfPatches = 0
# Logger
handlers = [logging.FileHandler('logger.log', mode="w"), logging.StreamHandler()]
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s', datefmt="%H:%M:%S",
                    handlers=handlers)

# Dirs
projectDir = os.getcwd()
inputFolder = os.path.join(projectDir, "input")
outputFolder = os.path.join(projectDir, "output")

# Page details

# Single page dimensions

cropDimensions = {"A1": {"x1": 1000, "y1": 350, "x2": 2750, "y2": 2800, "margin": 200, "pageNum": 2},
                  "A2": {"x1": 1000, "y1": 550, "x2": 3300, "y2": 3650, "margin": 800, "pageNum": 2},
                  "B": {"x1": 700, "y1": 400, "x2": 2800, "y2": 3600, "margin": 300, "pageNum": 2},
                  "I": {"x1": 750, "y1": 700, "x2": 3200, "y2": 4500, "margin": 0, "pageNum": 1}
                  }
patchDimensions = {"x": 300, "y": 200, "xOffset": 100, "yOffset": 200 // 3}

numOfThreads = 3


def cropSinglePage(imageName: str, dimensionsDict: dict, folderName: str):
    img = cv2.imread(os.path.join(inputFolder, folderName, imageName), cv2.IMREAD_GRAYSCALE)
    originalName = imageName
    x1 = dimensionsDict["x1"]
    x2 = dimensionsDict["x2"]
    y1 = dimensionsDict["y1"]
    y2 = dimensionsDict["y2"]
    delta = dimensionsDict["x2"] - dimensionsDict["x1"]
    for _ in range(dimensionsDict["pageNum"]):
        croppedImage = img[y1:y2, x1:x2]
        # saveLocation = os.path.join(outputFolder, imageName) 
        saveName = imageName[:-4]  # Get the name of the image without the extension (e.g. without '.jpg')
        cropToPatches(croppedImage, saveName, dimensionsDict["x2"] - dimensionsDict["x1"],
                      dimensionsDict["y2"] - dimensionsDict["y1"], folderName)
        # cv2.imwrite(saveLocation, croppedImage)
        x1 += delta + dimensionsDict["margin"]
        x2 += delta + dimensionsDict["margin"]
        imageName = imageName[:-4] + "2.jpg"
    global numOfImagesCropped
    numOfImagesCropped += 1
    logging.info("Image " + originalName + " Cropped successfully.")


def cropFiles(imagesInput, dimensionsDict: dict, folderName: str):
    for imageName in imagesInput:
        cropSinglePage(imageName, dimensionsDict, folderName)


def listToChunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def runThreads(folderName: str, dimensionsDict: dict):
    path = os.path.join(inputFolder, folderName)
    try:
        imagesInput = os.listdir(path)
    except FileNotFoundError:
        logging.error("Input file '" + path + "' not found.")
        return
    if not os.path.exists(outputFolder):
        os.mkdir(outputFolder)
    if not os.path.exists(os.path.join(outputFolder, folderName)):
        os.mkdir(os.path.join(outputFolder, folderName))
    i = round(len(imagesInput) // (numOfThreads - 1))
    chunks = list(listToChunks(imagesInput, i))
    with concurrent.futures.ThreadPoolExecutor(max_workers=numOfThreads) as executor:
        for i in range(numOfThreads):
            executor.submit(cropFiles, chunks[i], dimensionsDict, folderName)


def cropToPatches(image, imageName: str, xDelta: int, yDelta: int, folderName: str):
    # image = cv2.imread(os.path.join(outputFolder, imageName))
    patchCount = 0
    x1 = y1 = 0
    x2, y2 = patchDimensions["x"], patchDimensions["y"]
    xOffset, yOffset = patchDimensions["xOffset"], patchDimensions["yOffset"]
    i = 1
    while x2 < xDelta and patchCount < 10:
        j = 0
        while y2 + yOffset * j < yDelta and patchCount < 10:
            croppedPatch = image[y1 + yOffset * j: y2 + yOffset * j, x1: x2]
            saveLocation = os.path.join(outputFolder, folderName, imageName + "_" + str(i) + ".jpg")
            global numOfPatches
            numOfPatches += 1
            cv2.imwrite(saveLocation, croppedPatch)
            i += 1
            j += 1
            patchCount += 1
        x1 += xOffset
        x2 += xOffset


def preProcessingMain():
    try:
        foldersName = os.listdir(inputFolder)
    except FileNotFoundError:
        logging.error("Input file '" + inputFolder + "' not found.")
        return
    for name in foldersName:
        logging.info("Start cropping the folder " + name + ".")
        try:
            runThreads(name, cropDimensions[name])
            logging.info("Cropping of " + name + " succeeded.")
        except KeyError:
            logging.error("File name doesn't match to the dictionary's key.")
            logging.error("Cropping of " + name + " Failed.")


def main():
    startTime = datetime.now()
    logging.info("PreProcessing Script started")
    preProcessingMain()
    logging.info("PreProcessing Script ended, execution time: " + str(datetime.now() - startTime))
    logging.info(str(numOfImagesCropped) + " Images have been cropped into " + str(numOfPatches) + " Patches.")


if __name__ == "__main__":
    main()