import cv2


def draw_on_image(bbox, img, color=(0, 255, 0)):

    cv2.rectangle(img, (bbox.x, bbox.y), (bbox.x + bbox.w, bbox.y + bbox.h), color, 2)

    label = ""
    if bbox.identifier is not None:
        label += "id: {} ".format(bbox.identifier)

    if bbox.confidence is not None:
        label += "conf: {}".format(bbox.confidence)

    if len(label):
        cv2.putText(img, label, (bbox.x + 5, bbox.y - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)