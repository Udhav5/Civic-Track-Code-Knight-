navigator.geolocation.getCurrentPosition(pos => {
  const lat = pos.coords.latitude;
  const lon = pos.coords.longitude;

  const map = L.map('map').setView([lat, lon], 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  fetch(`/api/issues-html?lat=${lat}&lon=${lon}&distance=5`)
    .then(res => res.text())  
    .then(scriptText => {
      eval(scriptText); 
      
      issues.forEach(issue => {
        L.marker([issue.lat, issue.lon]).addTo(map)
          .bindPopup(`<b>${issue.title}</b><br>${issue.category}<br>Status: ${issue.status}`);
      });
    });
}, error => {
  alert("Location access is required for this map.");
});
