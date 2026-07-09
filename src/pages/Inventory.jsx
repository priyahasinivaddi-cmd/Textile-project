import { useEffect, useState } from "react";
import { getInventory } from "../services/inventoryService";

function Inventory() {
  const [data, setData] = useState([]);

  useEffect(() => {
    getInventory().then((res) => setData(res.data));
  }, []);

  return (
    <div className="p-6">
      <div className="overflow-x-auto rounded-3xl bg-white p-6 shadow-xl ring-1 ring-slate-200">
        <h2 className="text-2xl font-black text-slate-950">Inventory</h2>
        <table className="mt-4 min-w-full text-left text-sm">
          <thead className="text-slate-500">
            <tr>
              <th className="p-3">Batch ID</th>
              <th className="p-3">Fabric</th>
              <th className="p-3">Source</th>
              <th className="p-3">Quantity</th>
              <th className="p-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.id} className="border-t border-slate-100">
                <td className="p-3 font-bold">{item.waste_batch_id}</td>
                <td className="p-3">{item.fabric_type}</td>
                <td className="p-3">{item.source}</td>
                <td className="p-3">{item.quantity}</td>
                <td className="p-3">{item.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Inventory;
