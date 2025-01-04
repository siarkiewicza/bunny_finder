import React, { useState } from 'react';

const ImageUpload = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [results, setResults] = useState(null);

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(URL.createObjectURL(file));
      
      // Create form data
      const formData = new FormData();
      formData.append('image', file);

      try {
        // Send to backend
        const response = await fetch('http://localhost:5001/detect', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        setResults(data);
        console.log('Detection results:', data);
      } catch (error) {
        console.error('Error:', error);
      }
    }
  };

  return (
    <div className="image-upload">
      <input
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
      />
      {selectedImage && (
        <div>
          <img 
            src={selectedImage} 
            alt="Selected" 
            style={{ maxWidth: '500px' }} 
          />
        </div>
      )}
      {results && (
        <div>
          <h3>Detection Results:</h3>
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;