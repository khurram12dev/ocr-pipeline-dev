from typing import Any
import cv2
import numpy as np

class TextFluctuationClassifier:
    def __init__(self, image):
        self.image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self.processedImage = None

    def preprocess(self):
        # Preprocess the image (e.g., thresholding, noise reduction)
        _, processed = cv2.threshold(self.image, 128, 255, cv2.THRESH_BINARY_INV)
        self.processedImage = processed

    def detect_baseline_fluctuation(self):
        # A simplified method to detect baseline fluctuation
        # In a real-world scenario, this would be more complex
        rows, _ = self.processedImage.shape
        fluctuations = []

        for row in range(rows):
            if np.any(self.processedImage[row] == 255):
                fluctuations.append(row)

        fluctuation_range = max(fluctuations) - min(fluctuations)
        return fluctuation_range

    def classify_text(self):
        self.preprocess()
        fluctuation = self.detect_baseline_fluctuation()
        # print(fluctuation)

        # Set a threshold for fluctuation to classify between handwritten and digital
        # This threshold value might need adjustments based on experimentation
        if fluctuation > 55:  # Assuming 55 as a threshold for fluctuation
            return "Handwritten"
        else:
            return "Digital"

class TextSpacingClassifier:
    def __init__(self, image):
        self.image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def preprocess(self):
        # Convert to binary image
        _, thresh = cv2.threshold(self.image, 128, 255, cv2.THRESH_BINARY_INV)
        return thresh

    def detect_characters(self, image):
        # Find contours which could be individual characters
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def analyze_spacing_and_overlap(self, contours):
        # Analyze spacing and overlap
        bounding_boxes = [cv2.boundingRect(contour) for contour in contours]
        overlaps = 0
        spacings = []

        for i in range(len(bounding_boxes)):
            for j in range(i + 1, len(bounding_boxes)):
                if self.is_overlapping(bounding_boxes[i], bounding_boxes[j]):
                    overlaps += 1
                else:
                    spacing = self.calculate_spacing(bounding_boxes[i], bounding_boxes[j])
                    spacings.append(spacing)

        return overlaps, spacings

    def is_overlapping(self, box1, box2):
        # Check if two bounding boxes overlap
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        if x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2:
            return True
        return False

    def calculate_spacing(self, box1, box2):
        # Calculate horizontal spacing between boxes
        x1, _, w1, _ = box1
        x2, _, _, _ = box2

        return abs(x2 - (x1 + w1))

    def classify_text(self):
        processed_image = self.preprocess()
        contours = self.detect_characters(processed_image)
        overlaps, spacings = self.analyze_spacing_and_overlap(contours)
        # print({'overlaps':overlaps,'spacings':np.var(spacings)})

        # Classification based on overlap and spacing irregularities
        # Thresholds can be adjusted based on experimentation
        if overlaps > 5 and np.var(spacings) > 10000:  # Example thresholds
            return "Handwritten"
        else:
            return "Digital"

class TextContourClassifier:
    def __init__(self, image):
        self.image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self.processedImage = None

    def preprocess(self):
        # Convert to binary image and find edges
        _, thresh = cv2.threshold(self.image, 128, 255, cv2.THRESH_BINARY_INV)
        self.processedImage = thresh

    def analyze_contours(self):
        # Find contours
        contours, _ = cv2.findContours(self.processedImage, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Analyze contours for convexity and concavity
        contour_features = []
        for contour in contours:
            convex_hull = cv2.convexHull(contour, returnPoints=False)
            defects = cv2.convexityDefects(contour, convex_hull)
            
            if defects is not None:
                for i in range(defects.shape[0]):
                    s, e, f, d = defects[i, 0]
                    contour_features.append(d)  # Depth of defect

        return contour_features

    def classify_text(self):
        self.preprocess()
        features = self.analyze_contours()
        # print(features)

        # Classification based on features
        # This threshold and logic can be adjusted based on experimentation
        if len(features) > 5 and np.mean(features) > 1000:  # Example thresholds
            return "Handwritten"
        else:
            return "Digital"

class VotingClassifier:
    def __init__(self, image):
        # Initializing classifiers with the same image path
        self.classifiers = [
            TextContourClassifier(image),
            TextFluctuationClassifier(image),
            TextSpacingClassifier(image)
        ]

    def classify_text(self):
        # Dictionary to count votes for each class
        votes = {"Handwritten": 0, "Digital": 0}

        # Classify text using each classifier and tally votes
        for classifier in self.classifiers:
            result = classifier.classify_text()
            votes[result] += 1

        # Return the dictionary of votes and the class with the majority of votes
        return votes, max(votes, key=votes.get)

class SignatureDetectionPipeline:
    def __init__(self):
        pass
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass
    
    
    def run(self, image):

        # Run the classification process and print the results
        self.voting_classifier = VotingClassifier(image)
        votes, result = self.voting_classifier.classify_text()
        return result
