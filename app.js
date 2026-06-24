import { db } from "./firebase.js";
import { collection, getDocs } from "https://www.gstatic.com/firebasejs/10.0.0/firebase-firestore.js";

async function carregarDados() {
  const snapshot = await getDocs(collection(db, "contratos"));

  snapshot.forEach(doc => {
    console.log(doc.data());
  });
}

carregarDados();
