"""
Read FLUKA USRBIN binary output
  by xiaosj
"""

import numpy as np

# Head of USRBIN file
summaryHeadType = np.dtype([
        ('Title',  'a80'),
        ('Time',   'a32'),
        ('Weight', np.float32),
        ('Prime',  np.int32),
        ('mcase',  np.int32),
        ('nbatch', np.int32)
])


# Head of each record
recordHeadType = np.dtype([
    ('MB', np.int32),
    ('idx', np.int32),
    ('Name', 'a10'),
    ('binType', np.int32),
    ('particleType', np.int32),
    ('x0', np.float32),  # lower bound of X or R
    ('x1', np.float32),  # upper bound of X or R
    ('nx', np.int32),    # number of bins for X or R
    ('dx', np.float32),  # delta of bins for X or R
    ('y0', np.float32),  # lower bound of Y or Phi
    ('y1', np.float32),  # upper bound of Y or Phi
    ('ny', np.int32),    # number of bins for Y or Phi
    ('dy', np.float32),  # delta of bins for Y or Phi
    ('z0', np.float32),  # lower bound of Z
    ('z1', np.float32),  # upper bound of Z
    ('nz', np.int32),    # number of bins for Z
    ('dz', np.float32),  # delta of bins for Z
    ('lntzer', np.float32),
    ('Birk1', np.float32),
    ('Birk2', np.float32),
    ('timeCutOff', np.float32)
])


class usrbin:
    data = None
    error = None

    def setSummary(self, s):
        self.summary = s['Title'][0].decode('ascii')
        self.time = s['Time'][0].decode('ascii')
        self.totalWeight = s['Weight'][0]
        self._prime = s['Prime'][0]
        self._mcase = s['mcase'][0]
        self.totalPrime  = s['Prime'][0] + np.int64(s['mcase'][0])*1000000000
        self.nbatch = s['nbatch'][0]

    def setRecordHead(self, h):
        self.MB = h['MB'][0]
        self.idx = h['idx'][0]
        self.name = h['Name'][0].decode('ascii')
        self.binType = h['binType'][0]
        self.particleType = h['particleType'][0]
        self.x0 = h['x0'][0]
        self.x1 = h['x1'][0]
        self.nx = h['nx'][0]
        self.dx = h['dx'][0]
        self.y0 = h['y0'][0]
        self.y1 = h['y1'][0]
        self.ny = h['ny'][0]
        self.dy = h['dy'][0]
        self.z0 = h['z0'][0]
        self.z1 = h['z1'][0]
        self.nz = h['nz'][0]
        self.dz = h['dz'][0]
        self.lntzer = h['lntzer'][0]
        self.Birk1 = h['Birk1'][0]
        self.Birk2 = h['Birk2'][0]
        self.timeCutOff = h['timeCutOff'][0]
        self.shape = (self.nx, self.ny, self.nz)
        self.grid = (self.dx, self.dy, self.dz)


    def write(self, filename):
        try:
            f = open(filename, 'wb')
        except:
            raise Exception('Fail to open {:s}'.format(filename))
        
        # Write summary head
        f.write(b'\x80\x00\x00\x00')
        f.write(self.summary.encode('ascii'))
        f.write(self.time.encode('ascii'))
        f.write(self.totalWeight)
        f.write(self._prime)
        f.write(self._mcase)
        f.write(self.nbatch)

        # Write record head
        f.write(b'\x80\x00\x00\x00')
        f.write(self.MB)
        f.write(self.idx)
        f.write(self.name.encode('ascii'))
        f.write(self.binType)
        f.write(self.particleType)
        f.write(self.x0)
        f.write(self.x1)
        f.write(self.nx)
        f.write(self.dx)
        f.write(self.y0)
        f.write(self.y1)
        f.write(self.ny)
        f.write(self.dy)
        f.write(self.z0)
        f.write(self.z1)
        f.write(self.nz)
        f.write(self.dz)
        f.write(self.lntzer)
        f.write(self.Birk1)
        f.write(self.Birk2)
        f.write(self.timeCutOff)

        f.write(b'V\x00\x00\x00\x00e\x04\x00')
        dw = np.swapaxes(self.data, 0, 2)
        f.write(dw.tobytes())
        f.write(b'\x00e\x04\x00')

        f.write(b'\x0e\x00\x00\x00')
        f.write('STATISTICS'.encode('ascii'))
        f.write(b'\x01\x00\x00\x00')
        f.write(np.int32(14))
        f.write(b'\x00e\x04\x00')
        ew = np.swapaxes(self.error, 0, 2)
        f.write(ew.tobytes())
        f.write(b'\x00e\x04\x00')
        f.close()

#
# Read USRBIN binary file       
#
def ReadUsrbin(filename):
    try:
        f = open(filename, 'rb')
    except:
        raise Exception('Fail to open file')

    f.read(4)
    summary = np.fromfile(f, dtype=summaryHeadType, count=1)
    f.read(4)

    readError = False
    moreRecords = True
    usrbin_list = []
    
    while moreRecords:
        a = usrbin()
        a.setSummary(summary)
        
        head = np.fromfile(f, dtype=recordHeadType, count=1)
        a.setRecordHead(head)        
        f.read(8)
        
        data = np.fromfile(f, dtype=np.float32, count=a.nx*a.ny*a.nz)
        a.data = np.reshape(data, (a.nx,a.ny,a.nz), order='F')
        f.read(4)

        usrbin_list.append(a)

        skip = f.read(14)
        if skip==b'':
            moreRecords = False
        try:
            s = str(skip[-10:], 'ascii')
            if s == 'STATISTICS':
                moreRecords = False
                readError = True
            else:
                f.seek(-14,1)
        except:
            f.seek(-14,1)

    if readError:
        f.read(12)  # skip 4 + int32 + 4
        for i in range(len(usrbin_list)):
            a = usrbin_list[i]
            a.error = np.reshape(
                np.fromfile(f, dtype=np.float32, count=a.nx*a.ny*a.nz),
                (a.nx,a.ny,a.nz), order='F')
            f.read(8)

    return usrbin_list
