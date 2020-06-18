import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.ObjectOutputStream;
import java.io.Reader;
import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Queue;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;
import org.jsoup.nodes.Element;

public class Mapper {
	public String root_directory;
	public Queue<String> directoryQ;
	public List<Document> htmlDocs;
	public char[] punctuation = { '\"', ',', '.', '!', '?', ';', ':'};
	public List<String> stop_words;
	public List<String> exceptions;
	public List<ArrayList<String>> blocuri;
	public BufferedWriter mapW;
	public HashMap<String,List<String>> mapHm;

	public Mapper(String directory_path)
	{
		this.root_directory = new String(directory_path);
		this.directoryQ = new LinkedList<String>();
		this.directoryQ.add(this.root_directory);
		this.stop_words = new ArrayList<String>();
		this.blocuri = new ArrayList<ArrayList<String>>();
		this.mapHm = new HashMap<String, List<String>>();
		try {
			this.mapW = new BufferedWriter(new FileWriter("out/Map.txt"));
		} catch (IOException e1) {
			e1.printStackTrace();
		}
		File file = new File("stop_words.txt"); 
		BufferedReader br = null;
		try {
			br = new BufferedReader(new FileReader(file));
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} 
		String st; 
		try {
			while ((st = br.readLine()) != null) 
			{
				this.stop_words.add(st);
			}
		} catch (IOException e) {
			e.printStackTrace();
		} 		
		this.exceptions = new ArrayList<String>();
		file = new File("exceptions.txt"); 
		br = null;
		try {
			br = new BufferedReader(new FileReader(file));
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} 
		try {
			while ((st = br.readLine()) != null) 
			{
				this.exceptions.add(st);
			}
		} catch (IOException e) {
			e.printStackTrace();
		} 		
	}
	
	public boolean isPunctuation(char ch)
	{
		for (char c : punctuation) {
		    if (c == ch) 
		    {
		        return true;
		    }
		}
		return false;
	}
	
	public void getFiles()
	{
		ArrayList<String> fileNames  = new ArrayList<String>();
		while (!directoryQ.isEmpty())
		{
			File director = new File(directoryQ.element());
			directoryQ.remove();
			File[] listOfFiles = director.listFiles();
			
			for (File file : listOfFiles) {
			    if (file.isFile()) 
			    {			    	
		    		fileNames.add(file.getPath());	// adaug fisier	
			    }
			    if (file.isDirectory())
			    {
			    	directoryQ.add(file.getPath());
			    }
			}
			blocuri.add(fileNames);
    		fileNames = new ArrayList<String>();
		}
	}
	
	public void map(ArrayList<String> bloc)
	{
		// TODO: MAP FILE PENTRU FIECARE FISIER DINTR-UN BLOC
		// dupa maparea tuturor fisierelor din bloc se creeaza indexul invers
		int index = blocuri.indexOf(bloc);
		HashMap<String, List<String>> blocHM = new HashMap<String, List<String>>();
		for (String fisier : bloc)
		{
			HashMap<String, Integer> hm = this.mapFile(fisier);
			for (String key : hm.keySet())
			{
				if (blocHM.containsKey(key))
				{
					List<String> val = blocHM.get(key);
					val.add("(" + fisier + ", " + hm.get(key)+")");
					blocHM.put(key, val);
				}
				else
				{
					List<String> val = new ArrayList<String>();
					val.add("(" + fisier + ", " + hm.get(key)+")");
					blocHM.put(key, val);
				}
			}

		}
		try {
			BufferedWriter writer = new BufferedWriter(new FileWriter("out/Block_"+index+".txt"));
			for (String key: blocHM.keySet())
			{
				writer.write((key + ": "));
				for (String valoare: blocHM.get(key))
				{
					writer.write(valoare + ", ");
				}
				writer.write("\r\n");
				if (mapHm.containsKey(key))
				{
					List<String> val = mapHm.get(key);
					val.add("out/Block_"+index+".txt");
					mapHm.put(key, val);
					
				}
				else
				{
					List<String> val = new ArrayList<String>();
					val.add("out/Block_"+index+".txt");
					mapHm.put(key, val);
				}
			}
			writer.close();
		}
		catch (Exception e)
		{
			e.printStackTrace();
		}
		
	}
	
	public void writeMap()
	{
		for (String key : mapHm.keySet())
		{
			try {
				mapW.write(key + ": ");
				for (String bloc: mapHm.get(key))
				{
					mapW.write(bloc + ", ");
				}
				mapW.write("\r\n");
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
	}
	
	public boolean isException(String word)
	{
		if (this.exceptions.indexOf(word) != -1)
		{
			return true;
		}
		return false;
	}
	
	public boolean isStopWord(String word)
	{
		if (this.stop_words.indexOf(word) != -1)
		{
			return true;
		}
		return false;
	}
	
	public HashMap<String, Integer> mapFile(String filename)
	{
		HashMap<String, Integer> hm = new HashMap<String, Integer>();
		InputStream in = null;
		try {
			in = new FileInputStream(filename);
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
        Reader reader = null;
		try {
			reader = new InputStreamReader(in, "UTF-8");
		} catch (UnsupportedEncodingException e1) {
			e1.printStackTrace();
		}
        int r;
        StringBuilder sb = new StringBuilder();
        StringBuilder lower_sb = new StringBuilder();
        try {
			while ((r = reader.read()) != -1) {
			    char ch = (char) r;
			    char lch = Character.toLowerCase(ch);
			    if (Character.isWhitespace(ch) || isPunctuation(ch))
			    {
			    	if (sb.length() != 0)	// doar daca stringul nu e gol
			    	{
				    	// daca e spatiu sau punctuatie, se termina cuvantul
				    	// adauga la HashMap
				    	String s = sb.toString();
				    	String lower_s = lower_sb.toString();
				    	if (isException(s))
				    	{
				    		// e exceptie					    	
				    		// nu e stop word
					    	int val = 0;
					    	if (hm.containsKey(s))
					    	{
					    		val = hm.get(s);
					    	}
					    	hm.put(s, val + 1);
					    	// reinitializeaza StringBuilderul
					    	sb = new StringBuilder();
					    	lower_sb = new StringBuilder();
				    	}
				    	else
				    	{
				    		if (!this.isStopWord(s))
					    	{
					    		// nu e stop word
						    	int val = 0;
						    	if (hm.containsKey(lower_s))
						    	{
						    		val = hm.get(lower_s);
						    	}
						    	hm.put(lower_s, val + 1);
						    	// reinitializeaza StringBuilderul
						    	sb = new StringBuilder();
						    	lower_sb = new StringBuilder();
					    	}
				    		else
				    		{
				    			sb = new StringBuilder();
				    			lower_sb = new StringBuilder();
				    		}
				    	}
			    	}
			    }
			    else
			    {
			    	sb.append(ch);
			    	lower_sb.append(lch);
			    }
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
        return hm;
	}
	
	public void readMap(String filename)		// se citeste Map.txt din directorul out
	{
		InputStream in = null;
		try {
			in = new FileInputStream(filename);
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
        Reader reader = null;
		try {
			reader = new InputStreamReader(in, "UTF-8");
		} catch (UnsupportedEncodingException e1) {
			e1.printStackTrace();
		}
		int r;
		StringBuilder sb = new StringBuilder();
		mapHm = new HashMap<String, List<String>>();
		String lastKey = "";
		String lastVal = "";
		try {
			while ((r = reader.read()) != -1) 
			{
				char ch = (char) r;
				if (ch == ':')
				{
					lastKey = sb.toString();
					sb = new StringBuilder();
				}
				else if (ch == ',')
				{
					List<String> val = mapHm.get(lastKey);
					lastVal = sb.toString();
					if (val == null)
					{
						val = new ArrayList<String>();
					}
					val.add(lastVal);
					mapHm.put(lastKey, val);
					sb = new StringBuilder();
				}
				else if (ch == '\n')
				{
					sb = new StringBuilder();
				}
				else if (ch == ' ')
				{
					continue;
				}
				else
				{
					sb.append(ch);
				}
			}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	public HashMap<String, List<String>> readIndex(String filename)		// se citeste Map.txt din directorul out
	{
		InputStream in = null;
		try {
			in = new FileInputStream(filename);
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
        Reader reader = null;
		try {
			reader = new InputStreamReader(in, "UTF-8");
		} catch (UnsupportedEncodingException e1) {
			e1.printStackTrace();
		}
		int r;
		StringBuilder sb = new StringBuilder();
		HashMap<String, List<String>> map = new HashMap<String, List<String>>();
		String lastKey = "";
		String lastVal = "";
		try {
			while ((r = reader.read()) != -1) 
			{
				char ch = (char) r;
				if (ch == ':')
				{
					lastKey = sb.toString();
					sb = new StringBuilder();
				}
				else if (ch == ',')
				{
					List<String> val = map.get(lastKey);
					lastVal = sb.toString();
					if (val == null)
					{
						val = new ArrayList<String>();
					}
					val.add(lastVal);
					map.put(lastKey, val);
					sb = new StringBuilder();
				}
				else if (ch == '\n')
				{
					sb = new StringBuilder();
				}
				else if (ch == ' ')
				{
					continue;
				}
				else
				{
					sb.append(ch);
				}
			}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return map;
	}
	
	public boolean validate(String key)
	{
		if (isException(key) || (!isException(key) && !isStopWord(key)))
		{
			return true;
		}
		return false;
	}
	
	
	private List<String> getBlockCorespondent(String key, String filename)
	{
		HashMap<String, List<String>> blocHm = readIndex(filename);
		return blocHm.get(key);
	}
	
	private List<String> corespondent(String key)
	{
		List<String> blocuri = mapHm.get(key);
		// TODO: REUNESTE BLOCURI SI ADAUGA
		return null;
	}
	
	public List<String> andOperator(String key1, String key2)
	{
		// TODO:
		boolean ok1, ok2;
		ok1 = validate(key1);
		ok2 = validate(key2);
		if (ok1 && ok2)
		{
			// aplic operator
		}
		else
		{
			if (ok1)
			{
				// returnez corespondent key1
			}
			else if (ok2)
			{
				// returnez corespondent key2
			}
			else
			{
				// returnez lista goala
			}
		}
		return null;
	}

	public void booleanSearch() {
		BufferedReader reader =  new BufferedReader(new InputStreamReader(System.in)); 
	     // Reading data using readLine 
	     try {
	    	 char ch;
	    	 StringBuilder sb = new StringBuilder();
	    	 List<String> chei = new ArrayList<String>();
	    	 List<Character> op = new ArrayList<Character>();
	    	 while ((ch = (char)reader.read()) != '\n') 
	    	 {
	    		 if (ch == ' ' || ch == '.' || ch == ',')	// operator
	    		 {
	    			 chei.add(sb.toString());
	    			 op.add(ch);
	    			 sb = new StringBuilder();
	    		 }
	    		 else
	    		 {
	    			 sb.append(ch);
	    		 }
	    	 }
	    	 chei.add(sb.toString());
	    	 
		} catch (IOException e) {
			e.printStackTrace();
		} 
		
	}
	
	public static void main(String[] args) {
		Mapper m  = new Mapper("test-files");
		m.getFiles();
		for (ArrayList<String> bloc : m.blocuri)
		{
			m.map(bloc);
		}
		m.writeMap();
		m.readMap("out/Map.txt");
		m.booleanSearch();
//		for (String key: m.mapHm.keySet())
//		{
//			System.out.print(key + ": ");
//			for (String val: m.mapHm.get(key))
//			{
//				System.out.print(val + ", ");
//			}
//			System.out.print("\r\n");
//		}
		
	}

	

}
