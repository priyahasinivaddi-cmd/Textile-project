import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <div className="sidebar">
      <h3>Menu</h3>

      <p><Link to="/dashboard">Dashboard</Link></p>
      <p><Link to="/inventory">Inventory</Link></p>
      <p><Link to="/upload">Upload Waste</Link></p>
    </div>
  );
}

export default Sidebar;