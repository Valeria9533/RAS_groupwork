import numpy as np
import cv2
import imutils
import time
import tellopy
#import av
from djitellopy import Tello

drone = Tello()

try:
    drone.connect()
    drone.wait_for_connection(60.0)
except Exception as ex:
    print(ex)

#drone.streamon()
#print("Hello hello hello")
#frame_read = drone.get_frame_read()

#camera = frame_read
#print("before")
#camera = av.open(drone.get_video_stream())
#print("after")
#time.sleep(5)
try:
    drone.takeoff()
except:
    drone.land()

#time.sleep(10)

drone.streamon()




while (True):
    
    camera = drone.get_frame_read()
    
    # get_corners():
    ### Grabbing the video feed, "has frames" and "grabbed" check if
    ###there's a next frame, if there isn't, the feed will stop

    ### We'll have "img" and "image" for different purposes. "image" is the
    ### original video on top of which we draw, "img" is the one masked and
    ### used for getting contours to know what to draw.
    #try:
    print("Camera try")
    img = camera.frame
    image = camera.frame
    cv2.imwrite("img.png", img)
    if img is None:
         print("none")
         continue
    #except:
    #    print("Camera fail")
    #    continue
        #hasFrames, image = camera.read()
    #except:
    #    drone.land()
    #grabbed, img = camera.read()
    #image = img
    ### Changing the frame into hsv colors and blurring it in various ways to smoothen

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    blur_hsv = cv2.GaussianBlur(hsv, (1,1),0)
    blur_hsv = cv2.medianBlur(blur_hsv, 5)


    ### Create a white mask of the shape and blur the hell out of it

    mask = cv2.inRange(blur_hsv,(33, 90, 90), (80, 255, 255) )

    blur_mask = cv2.GaussianBlur(mask, (1, 1), 0)
    blur_mask = cv2.medianBlur(blur_mask, 21)

    kernel = np.ones((11, 11), np.float32) * 255
    kernelImg = np.zeros([50, 50, 3], dtype=np.uint8)
    kernelImg.fill(255)

    mask = cv2.erode(blur_mask, kernel, iterations=3)

    mask = cv2.dilate(blur_mask, kernel, iterations=3)


    ###Resulting "img" used for contour counting
    img = blur_mask
    #cv2.imshow('showing', img)


    ### Gets edges and makes contours out of them and sorts them into a list
    edged = cv2.Canny(img, 10, 550)
    edged = cv2.medianBlur(edged, 1)
    #cv2.imshow('Filming', edged)

    cnts = cv2.findContours(img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    #hull = np.array([[[5,5]],[[5,5]]])

    ### Empty list to be used later
    lista = np.array([])
    count = 0

    ###
    for c in cnts:

        ### approximate the contour and set minimum length fo rrecongised contours
        peri = cv2.arcLength(c, True)
        if peri >= 410:
            print("contours")
            approx = cv2.approxPolyDP(c, 0.05 * peri, True)

            ### Collect long enough contours into the list
            lista = np.append(lista,approx).astype(int)
            count += len(approx)

        else:
            continue

        ### If there are between 4 and 10 corners, draw the contour on the "image"
        if len(approx) >= 4 and len(approx) <= 10:
            cv2.imwrite("Test.png", image)
            cv2.drawContours(image, [approx], -1, (0, 0, 255), 5)

    try:
        ### This is "try", because all frames don't have contours and otherwise it would end the code
       print("try listing") 
       lista = np.reshape(lista, (count, 2))

    except:
        continue

    mask2 = cv2.inRange(image, (0, 0, 250), (0, 0, 255))
    gray = mask2
    
    inline = False
    inlevel = False
    centered = False

    try:
        ### Draw the connecting contour (green) and use convex hull to surround it to get outermost edges and corners
        print("trying to get contours")
        cv2.drawContours(image, [lista], -1, (0, 255, 0), 5)
        hull = cv2.convexHull(lista)
        cv2.drawContours(image,[hull], -1, (255,0,0),5)
        mask3 = cv2.inRange(image, (252, 0, 0), (255, 0, 0))

        corners = cv2.goodFeaturesToTrack(mask3, 4, 0.05, 110)
        corners = np.int0(corners)
        
        print("halfway contours")
        ### This get and draws he center of gate
        ret, labels, stats, centroids = cv2.connectedComponentsWithStats(mask3)
        mask3 = cv2.cvtColor(mask3, cv2.COLOR_GRAY2BGR)
        for i in centroids[1:]:
            cv2.rectangle(image, (int(i[0]), int(i[1])), (int(i[0] + 5), int(i[1] + 5)), (255, 0, 0), 3)
        ### And this gets the center of  image frame
        center_width = int(image.shape[1]/2)
        center_height = int(image.shape[0]/2)
        cv2.circle(image, (center_width, center_height), 10, (0, 0, 255), -1)
        print("end contours")
        ### Here we compare the two different centers to determine where to move
        
        if center_width - centroids[1][0] > 20:
            print('Fly Left')
            drone.move_left(1)
            
        elif center_width - centroids[1][0] < -20:
            print('Fly Right')
            drone.move_right(1)
            
        else:
            print('Stay in line')
            inline = True

        if center_height - centroids[1][1] > 20:
            print('Fly Up')
            drone.move_up(1)

        elif center_height - centroids[1][1] < -20:
            print('Fly Down')
            drone.move_down(1)
            
        else:
            print('Stay in Level')
            inlevel = True


        ### Draws yellow corners on "image"
        for i in corners:
            x, y = i.ravel()
            cv2.circle(image, (x, y), 1, (0,255,255), -1)


        target = [0,255,255]
        X,Y = np.array(np.where(np.all(image==target, axis=2)))

        coordinates = np.array([])
        for c in range(0,19,5):
            coordinates = np.append(coordinates,X[c])
            coordinates = np.append(coordinates, Y[c])

        coordinates = np.reshape(coordinates,(4,2))

    except:
        print("didn't get contours")
        continue

        #cv2.imshow("gate2", image)

        #time.sleep(0.05)

        #if cv2.waitKey(1) & 0xFF == ord('q'):
            #break


    #cv2.imshow("gate2", image)

    # cv2.imshow('Filming', img)
    #time.sleep(0.05)

    #if cv2.waitKey(1) & 0xFF == ord('q'):
        #break

    try:
        bot_left = np.argmin(coordinates[2:4,1]) + 2
        top_left = np.argmin(coordinates[0:2,1])
        bot_right = np.argmax(coordinates[2:4,1]) + 2
        top_right = np.argmax(coordinates[0:2,1])

        #print(coordinates[bot_left])
        #print(coordinates[2])
        if (coordinates[bot_left][0] - coordinates[top_left][0]) - (coordinates[bot_right][0] - coordinates[top_right][0]) >8:
            #print()
            #print('Rotate to Left ')
            #print()
            drone.counter_clockwise(5)
            
        if (coordinates[bot_right][0] - coordinates[top_right][0]) - (coordinates[bot_left][0] - coordinates[top_left][0]) >8:
            #print()
            #print('Rotate to Right ')
            #print()
            drone.clockwise(5)

        else:
            #print()
            #print('Centered')
            #print()
            centered = True

    except:
        continue
        
    if inline and inlevel and centered:
        drone.forward(100)
        break
        
time.sleep(5)
drone.land()
drone.quit()
#camera.release()
#cv2.destroyAllWindows()

