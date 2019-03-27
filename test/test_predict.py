from unet import *
from data import *
import numpy as np
import cv2

def create_test_data(FOLDER_image, out_rows=128, out_cols=128):
    i = 0
    print('-'*30)
    print('Creating test images...')
    print('-'*30)
    imgs = glob.glob(FOLDER_image+"/*.jpg")
    print(len(imgs))

    imgdatas = np.ndarray((len(imgs),out_rows,out_cols,1), dtype=np.uint8)
    for imgname in imgs:
        midname = imgname[imgname.rindex("/")+1:]
        img = load_img(imgname, grayscale=True)
        print img.size
        img = img_to_array(img)
        #img = cv2.imread(self.test_path + "/" + midname,cv2.IMREAD_GRAYSCALE)
        #img = np.array([img])
        # print img.shape
        imgdatas[i] = img
        i += 1
    return imgdatas

def sliding_window(image, stepSize, windowSize):
    # slide a window across the image
    for y in xrange(0, image.shape[0], stepSize):
        for x in xrange(0, image.shape[1], stepSize):
            # yield the current window
            yield (x, y, image[y:y + windowSize[1], x:x + windowSize[0]])



myunet = myUnet()
model = myunet.get_unet()
model.load_weights('unet-0102-512-gray.hdf5')

# imgs_mask_test = model.predict(imgs_test, verbose=1)
# imgs = imgs_mask_test
# for i in range(imgs.shape[0]):
#     img = imgs[i]
#     img = array_to_img(img)
#     x, y, w, h = LIST_position[i]
#     # print img.size
#     image_mask[y : y + h, x : x + w] = img
#     # img.save("results/%d.jpg"%(i))


FOLDER_test = '/media/hd01/zhilun/kaggle-canbin/dataset/valid_test'
LIST_images = glob.glob(FOLDER_test + '/*.jpg')
FOLDER_test = '/media/hd01/zhilun/kaggle-canbin/dataset/batch_7590'
LIST_images.extend(glob.glob(FOLDER_test + '/*.jpg'))
FOLDER_test = '/media/hd01/zhilun/kaggle-canbin/dataset/batch_7500'
LIST_images.extend(glob.glob(FOLDER_test + '/*.jpg'))

# LIST_images = glob.glob('rect/*.jpg')

for FILE_im in LIST_images:
    print FILE_im
    if os.path.exists('vis-batch/' + os.path.basename(FILE_im) + '.mask.jpg'): continue

    image = cv2.imread(FILE_im, 0)
    image = cv2.resize(image, (1690, 1119))
    
    pad = 0
    image = cv2.copyMakeBorder(image, pad, 500, pad, 500, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    image_vis = cv2.imread(FILE_im)
    image_vis = cv2.resize(image_vis, (1690, 1119)) 
    image_vis = cv2.copyMakeBorder(image_vis, pad, 500, pad, 500, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    image_mask = 255 * np.ones(image.shape[0 : 2])

    LIST_crops = list()
    LIST_position = list()
    (winW, winH) = (512, 512)
    for (x, y, window) in sliding_window(image, stepSize=512, windowSize=(winW, winH)):
        # if the window does not meet our desired window size, ignore it
        if window.shape[0] != winH or window.shape[1] != winW:

            continue
            # print window.shape
            # if y + winH >= image.shape[0] and x + winW >= image.shape[1]:
            #     image_crop = image[image.shape[0] - winH : image.shape[0], image.shape[1] - winW : image.shape[1]]
            #     LIST_position.append((image.shape[0] - winH, image.shape[1] - winW, winW, winH))
            # elif y + winH >= image.shape[0]:
            #     image_crop = image[image.shape[0] - winH : image.shape[0], x : x + winW]
            #     LIST_position.append((image.shape[0] - winH, x, winW, winH))
            # elif x + winW >= image.shape[1]:
            #     image_crop = image[y : y + winH, image.shape[1] - winW : image.shape[1]]
            #     LIST_position.append((y, image.shape[1] - winW, winW, winH))

            # continue
            # image_crop = 255 * np.ones((winW, winH))
            # print y, y + winH - window.shape[0]
            # print x, x + winW - window.shape[1]
            # image_crop[y : y + winH - window.shape[0], x : x + winW - window.shape[1]] = image[y : y + winH - window.shape[0], x : x + winW - window.shape[1]]
            
            # LIST_crops.append(image_crop)
            # LIST_position.append((x, y, winW, winH))

        else:
            image_crop = image[y : y + winH, x : x + winW]
            # image_crop = image_crop.astype('float32')
            # image_crop /= 255
            LIST_crops.append(image_crop)
            LIST_position.append((x, y, winW, winH))

            # imgdatas = np.ndarray((len(imgs),out_rows,out_cols,1), dtype=np.uint8)
            # for imgname in imgs:
            #     midname = imgname[imgname.rindex("/")+1:]
            #     img = load_img(imgname, grayscale=True)
            #     img = img_to_array(img)
            #     #img = cv2.imread(self.test_path + "/" + midname,cv2.IMREAD_GRAYSCALE)
            #     #img = np.array([img])
            #     # print img.shape
            #     imgdatas[i] = img
            #     i += 1


    # mydata = dataProcess(512,512)
    # imgs_test = create_test_data(FOLDER_test)
    # imgs_test = mydata.load_test_data()

    # print imgs_test.shape
    LIST_crops = np.asarray(LIST_crops).reshape(len(LIST_crops), 512, 512, 1).astype('float32')
    print LIST_crops.shape

    imgs_test = LIST_crops
    if len(imgs_test) >= 15: continue
    imgs_mask_test = model.predict(imgs_test, verbose=1)

    imgs = imgs_mask_test
    for i in range(imgs.shape[0]):
        img = imgs[i]
        img = array_to_img(img)
        x, y, w, h = LIST_position[i]
        # print img.size
        image_mask[y : y + h, x : x + w] = img
        # img.save("results/%d.jpg"%(i))

        # img_src = imgs_test[i]
        # img_src = array_to_img(img_src)
        # img_src.save("results/%d_src.jpg"%(i))


    # image_merge = np.hstack((image, 255 * image_mask))
    # image_merge = np.hstack((image_vis, cv2.cvtColor(np.asarray(255 * image_mask, dtype="float32"), cv2.COLOR_GRAY2RGB)))
    # image_merge = np.hstack((image_vis, cv2.cvtColor(np.asarray(image_mask, dtype="float32"), cv2.COLOR_GRAY2RGB)))

    image_vis = image_vis[ : -500, : -500]
    image_mask = image_mask[ : -500, : -500]
    cv2.imwrite('vis-batch/' + os.path.basename(FILE_im) + '.src.jpg', image_vis)
    cv2.imwrite('vis-batch/' + os.path.basename(FILE_im) + '.mask.jpg', image_mask)
