import { useState } from "react";
import API from "../services/api";

function UploadWaste() {
  const [form, setForm] = useState({
    batch_id: "",
    fabric_type: "",
    source: "",
    quantity: "",
    color: "",
    condition: "",
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await API.post("/inventory", form);
      alert("Waste uploaded successfully");
    } catch (err) {
      console.log(err);
      alert("Upload failed");
    }
  };

  return (
    <div>
      <h2>Upload Waste</h2>

      <form onSubmit={handleSubmit}>
        <input placeholder="Batch ID"
          onChange={(e) => setForm({...form, batch_id: e.target.value})} />

        <input placeholder="Fabric Type"
          onChange={(e) => setForm({...form, fabric_type: e.target.value})} />

        <input placeholder="Source"
          onChange={(e) => setForm({...form, source: e.target.value})} />

        <input placeholder="Quantity"
          onChange={(e) => setForm({...form, quantity: e.target.value})} />

        <input placeholder="Color"
          onChange={(e) => setForm({...form, color: e.target.value})} />

        <input placeholder="Condition"
          onChange={(e) => setForm({...form, condition: e.target.value})} />

        <button type="submit">Upload</button>
      </form>
    </div>
  );
}

export default UploadWaste;