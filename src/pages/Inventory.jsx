import { useEffect, useState } from "react";
import API from "../services/api";

function Inventory() {
  const [data, setData] = useState([]);

  useEffect(() => {
    API.get("/inventory")
      .then((res) => setData(res.data))
      .catch((err) => console.log(err));
  }, []);

  return (
    <div>
      <h2>Inventory</h2>

      <table border="1">
        <thead>
          <tr>
            <th>Batch ID</th>
            <th>Fabric</th>
            <th>Source</th>
            <th>Quantity</th>
            <th>Color</th>
            <th>Condition</th>
          </tr>
        </thead>

        <tbody>
          {data.map((item) => (
            <tr key={item.id}>
              <td>{item.batch_id}</td>
              <td>{item.fabric_type}</td>
              <td>{item.source}</td>
              <td>{item.quantity}</td>
              <td>{item.color}</td>
              <td>{item.condition}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Inventory;