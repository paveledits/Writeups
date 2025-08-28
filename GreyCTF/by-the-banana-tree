# GreyCTF-by-the-banana-tree
Writeup for the Flag "By The Banana Tree" OSINT category in the GreyCTF event

<img width="480" alt="image" src="https://github.com/user-attachments/assets/3c0d9e95-ca1e-4aff-ba78-c8d8471591fe" />

Here you can see the challenge description.
We need to first download the ZIP file and extract it. It conatains following image file.

[dist-by_the_banana_tree.zip](https://github.com/user-attachments/files/20540520/dist-by_the_banana_tree.zip)

![bythebananatree](https://github.com/user-attachments/assets/881dabee-96f4-44b2-baf8-345ac870f21d)

To find the exact coordinates of the image we need to look at the image first. 

![bythebananatree](https://github.com/user-attachments/assets/79cf5b32-c46d-4c63-9ebe-6c9baed8438f)

Here we can see the road name: **DT 317**

If we type that into google maps we find following:


<img width="438" alt="image" src="https://github.com/user-attachments/assets/579dd555-e947-465c-a114-26621ac9cedc" />


![Screenshot](https://github.com/user-attachments/assets/fa2d0c55-9364-4a8a-8b32-757f41246c43)


This is what we are working with. Since on the image we can also see that **QL32** is 12km away. 
This means that we need to look in there range where those 2 roads cross. 

After hours of manual search and frustaration that all churches in Vietnam look the same and that Google is too lazy to do street view in Vietnam we end up finding this 360 drone shot:


<img width="961" alt="image" src="https://github.com/user-attachments/assets/9a2c73fe-9e5b-45a8-9aa4-12592e587b7d" />


When pressing on it we can recognize some similarities with our original image.


![Screenshot](https://github.com/user-attachments/assets/56c726e7-373a-4dca-a054-886c4e624151)


We can see the church and the location, where the image was originally taken.

From here it just gets  _harder_.

Now we need to find the exact coords of where the image was taken down to about 50 meters.


<img width="848" alt="image" src="https://github.com/user-attachments/assets/5d9929e6-7ec1-429d-99ff-7b24f9549fe4" />


21.153124, 105.274440 rounded to 3 decimal points is N21-153_E105-274

Notice how I already applied the correct format to the coords like mentioned here:


<img width="439" alt="image" src="https://github.com/user-attachments/assets/bc75b8f4-57f5-4ec5-b8ed-4f637dbf0059" />


Then we also need to find the name of the Church which is called:


<img width="404" alt="image" src="https://github.com/user-attachments/assets/708faabb-3014-4753-96eb-8c6fafbf248b" />


Or **nhathothanhlam** without any spaces or diacritics.

If we put this together we get following flag!


### grey{N21-153_E105-274_nhathothanhlam}
